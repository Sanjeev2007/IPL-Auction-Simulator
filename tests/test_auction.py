"""Phase-1 backend core: rooms, bidding rules, lot resolution, roster handoff.

Drives the pure state machine directly (no WebSocket) — the transport layer in
phase 2 will exercise these same methods over the wire.
"""
import pytest

from scripts.run_tournament import build_teams, load_players
from src.simulation.league_engine import simulate_season
from src.auction import (
    AuctionManager,
    AuctionRoom,
    AuctionConfig,
    DEFAULT_CONFIG,
    CRORE,
    LAKH,
    catalog_from_players,
    to_team_roster,
    assemble_xi,
    RoomPhase,
    LotStatus,
    BidTooLowError,
    InsufficientBudgetError,
    SquadFullError,
    AlreadyHighBidderError,
    NoActiveLotError,
    InvalidActionError,
    CannotFieldXIError,
)


# ── fixtures / helpers ──────────────────────────────────────────────────────
@pytest.fixture
def catalog(players):
    return catalog_from_players(players)


def _bowler_ids(catalog, n):
    return [e.player_id for e in catalog.values() if e.can_bowl][:n]


def _non_bowler_ids(catalog, n):
    return [e.player_id for e in catalog.values() if not e.can_bowl][:n]


def _squad_ids(catalog, n, min_bowlers=3):
    """`n` distinct ids including at least `min_bowlers` bowl-capable players."""
    bowlers = _bowler_ids(catalog, min_bowlers)
    others = [pid for pid in catalog if pid not in bowlers]
    return bowlers + others[: n - min_bowlers]


def _room_with_two(catalog, config=DEFAULT_CONFIG, pool=None):
    room = AuctionRoom(catalog=catalog, config=config)
    p1 = room.add_participant("Alice", is_host=True)
    p2 = room.add_participant("Bob")
    room.start(room.host_token, player_ids=pool)
    return room, p1, p2


# ── bid validation ──────────────────────────────────────────────────────────
def test_first_bid_must_meet_base_price(catalog):
    room, p1, p2 = _room_with_two(catalog)
    base = room.active_lot.card.base_price
    assert room.min_next_bid() == base

    with pytest.raises(BidTooLowError):
        room.place_bid(p1.id, base - 25 * LAKH)

    ev = room.place_bid(p1.id, base)
    assert ev["type"] == "bid_placed"
    assert room.active_lot.current_bidder_id == p1.id


def test_below_increment_is_rejected(catalog):
    room, p1, p2 = _room_with_two(catalog)
    base = room.active_lot.card.base_price
    room.place_bid(p1.id, base)
    min_next = room.min_next_bid()
    assert min_next == base + DEFAULT_CONFIG.increment_for(base)

    with pytest.raises(BidTooLowError):
        room.place_bid(p2.id, min_next - 1)

    room.place_bid(p2.id, min_next)  # exactly the increment is allowed
    assert room.active_lot.current_bidder_id == p2.id


def test_over_budget_is_rejected(catalog):
    room, p1, p2 = _room_with_two(catalog)
    # Well above ₹100 cr but a legal raise, so only the budget rule can stop it.
    with pytest.raises(InsufficientBudgetError):
        room.place_bid(p1.id, 200 * CRORE)


def test_cannot_outbid_yourself(catalog):
    room, p1, p2 = _room_with_two(catalog)
    room.place_bid(p1.id, room.min_next_bid())
    with pytest.raises(AlreadyHighBidderError):
        room.place_bid(p1.id, room.min_next_bid())


def test_highest_bidder_wins_on_resolve(catalog):
    room, p1, p2 = _room_with_two(catalog)
    lot = room.active_lot
    player_id = lot.card.player_id
    base = lot.card.base_price

    room.place_bid(p1.id, base)
    winning = room.min_next_bid()
    room.place_bid(p2.id, winning)  # Bob is now top bidder

    ev = room.resolve_active_lot()
    assert ev["type"] == "lot_sold"
    assert ev["winner_id"] == p2.id
    assert ev["price"] == winning
    # Budget deducted, player added to the winner's squad only.
    assert p2.budget_remaining == DEFAULT_CONFIG.starting_budget - winning
    assert p1.budget_remaining == DEFAULT_CONFIG.starting_budget
    assert [e.card.player_id for e in p2.squad] == [player_id]
    assert p1.squad == []


def test_unsold_when_no_bids(catalog):
    room, p1, p2 = _room_with_two(catalog)
    idx = room.active_lot.index
    ev = room.resolve_active_lot()
    assert ev["type"] == "lot_unsold"
    assert room.lots[idx].status is LotStatus.UNSOLD
    # No budgets touched.
    assert p1.budget_remaining == p2.budget_remaining == DEFAULT_CONFIG.starting_budget


def test_bidding_requires_active_lot(catalog):
    room = AuctionRoom(catalog=catalog)
    p1 = room.add_participant("Alice", is_host=True)
    room.add_participant("Bob")
    with pytest.raises(NoActiveLotError):  # not started yet
        room.place_bid(p1.id, 2 * CRORE)


# ── squad-max rule + auto-complete when all squads full ─────────────────────
def test_squad_full_blocks_bidding_and_completes(catalog):
    pool = _squad_ids(catalog, 4, min_bowlers=2)  # 4 lots, tiny squad cap
    config = AuctionConfig(squad_max=1, squad_min=1)
    room = AuctionRoom(catalog=catalog, config=config)
    p1 = room.add_participant("Alice", is_host=True)
    p2 = room.add_participant("Bob")
    room.start(room.host_token, player_ids=pool)

    # Alice wins lot 0 → her squad is now full.
    room.place_bid(p1.id, room.active_lot.card.base_price)
    room.resolve_active_lot()
    assert p1.squad_size == 1

    # Alice can't bid on lot 1; Bob can and wins.
    with pytest.raises(SquadFullError):
        room.place_bid(p1.id, room.active_lot.card.base_price)
    room.place_bid(p2.id, room.active_lot.card.base_price)
    room.resolve_active_lot()

    # Both squads full → auction ends even though lots remain in the pool.
    assert room.phase is RoomPhase.COMPLETE
    assert room.active_lot is None


# ── room lifecycle via the manager: create → join → start → complete ────────
def test_room_lifecycle(catalog):
    mgr = AuctionManager(catalog=catalog)
    room, host = mgr.create_room("Alice")
    assert host.is_host and room.phase is RoomPhase.LOBBY
    assert host.budget_remaining == DEFAULT_CONFIG.starting_budget

    _, bob = mgr.join_room(room.code, "Bob")
    assert mgr.get_room(room.code) is room
    assert len(room.participants) == 2

    with pytest.raises(InvalidActionError):  # wrong host token
        room.start("not-the-token")

    pool = _squad_ids(catalog, 3, min_bowlers=1)
    room.start(room.host_token, player_ids=pool)
    assert room.phase is RoomPhase.IN_PROGRESS

    # Drive every lot to exhaustion → COMPLETE.
    guard = 0
    while room.phase is RoomPhase.IN_PROGRESS and guard < 50:
        room.resolve_active_lot()
        guard += 1
    assert room.phase is RoomPhase.COMPLETE
    assert room.active_lot is None


def test_start_needs_two_participants(catalog):
    mgr = AuctionManager(catalog=catalog)
    room, _ = mgr.create_room("Solo")
    with pytest.raises(InvalidActionError):
        room.start(room.host_token)


def test_cannot_join_after_start(catalog):
    room, p1, p2 = _room_with_two(catalog)
    with pytest.raises(InvalidActionError):
        room.add_participant("Latecomer")


# ── roster assembly: drafted squad → engine-accepted TeamRoster ─────────────
def test_assemble_xi_from_oversized_squad(catalog):
    ids = _squad_ids(catalog, 15, min_bowlers=5)
    cards = [catalog[pid].to_card() for pid in ids]
    batting_order, bowlers = assemble_xi(cards)

    assert len(batting_order) == 11
    assert len(set(batting_order)) == 11
    assert set(batting_order) <= set(ids)      # XI drawn from the squad
    assert len(bowlers) >= 1                     # engine's hard requirement
    assert set(bowlers) <= set(batting_order)   # bowlers are part of the XI


def test_to_team_roster_is_engine_accepted(players, catalog):
    ids = _squad_ids(catalog, 13, min_bowlers=4)
    cards = [catalog[pid].to_card() for pid in ids]
    roster = to_team_roster("TEAM_A", "Team A", cards)

    assert set(roster.keys()) == {"team_id", "name", "batting_order", "bowlers"}
    # The real engine builder accepts it without complaint.
    teams = build_teams(players, {roster["team_id"]: {
        "batting_order": roster["batting_order"],
        "bowlers": roster["bowlers"],
        "name": roster["name"],
    }})
    assert len(teams[0].playing_xi) == 11


def test_explicit_xi_override(catalog):
    ids = _squad_ids(catalog, 13, min_bowlers=4)
    cards = [catalog[pid].to_card() for pid in ids]
    chosen = ids[:11]
    roster = to_team_roster("T", "T", cards, explicit_xi=chosen)
    assert roster["batting_order"] == chosen          # order preserved as given
    assert all(pid in chosen for pid in roster["bowlers"])

    with pytest.raises(CannotFieldXIError):            # wrong size
        to_team_roster("T", "T", cards, explicit_xi=ids[:10])
    with pytest.raises(CannotFieldXIError):            # player not in squad
        to_team_roster("T", "T", cards[:11], explicit_xi=[cards[0].player_id] * 11)


def test_assemble_xi_rejects_short_squad(catalog):
    cards = [catalog[pid].to_card() for pid in _squad_ids(catalog, 8)]
    with pytest.raises(CannotFieldXIError):
        assemble_xi(cards)


# ── full handoff: draft two squads and simulate a season from them ──────────
def test_drafted_rosters_simulate_a_season(catalog):
    squad_a = _squad_ids(catalog, 11, min_bowlers=5)
    remaining = [pid for pid in catalog if pid not in squad_a]
    bowlers_b = [pid for pid in remaining if catalog[pid].can_bowl][:5]
    squad_b = bowlers_b + [pid for pid in remaining if pid not in bowlers_b][:6]

    config = AuctionConfig(squad_min=11, squad_max=11)
    room = AuctionRoom(catalog=catalog, config=config)
    p1 = room.add_participant("Alice", is_host=True)
    p2 = room.add_participant("Bob")
    room.start(room.host_token, player_ids=squad_a + squad_b)

    # Each lot goes to its intended owner at base price.
    owner_of = {pid: p1.id for pid in squad_a}
    owner_of.update({pid: p2.id for pid in squad_b})
    guard = 0
    while room.phase is RoomPhase.IN_PROGRESS and guard < 100:
        lot = room.active_lot
        room.place_bid(owner_of[lot.card.player_id], lot.card.base_price)
        room.resolve_active_lot()
        guard += 1

    assert p1.squad_size == 11 and p2.squad_size == 11

    out = room.assemble_rosters()
    assert out["skipped"] == []
    assert len(out["rosters"]) == 2

    # Real engine: build teams from the drafted rosters and simulate a season.
    roster_data = {
        r["team_id"]: {"batting_order": r["batting_order"], "bowlers": r["bowlers"], "name": r["name"]}
        for r in out["rosters"]
    }
    teams = build_teams(load_players(), roster_data)
    result = simulate_season(teams)
    assert result.champion is not None
