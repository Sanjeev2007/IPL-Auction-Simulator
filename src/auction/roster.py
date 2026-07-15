"""Turn a drafted squad into an engine-ready ``TeamRoster``.

The auction lets a participant draft up to ``squad_max`` players; the engine
needs exactly 11 in batting order plus a bowlers list (see
``build_teams`` in ``scripts/run_tournament.py`` and the ``TeamRoster`` schema
in ``src/api/server.py``). This module bridges the two:

* :func:`assemble_xi` — auto-pick the strongest legal XI, aiming for a keeper
  and enough bowlers, then order it.
* :func:`to_team_roster` — produce the exact dict ``simulate_season`` accepts,
  either from the auto XI or from a participant-supplied explicit XI (the
  phase-3 "manual override" screen).

Selection works purely off :class:`PlayerCard` data, so it needs no engine
imports and stays trivially testable.
"""

from __future__ import annotations

from src.auction.config import AuctionConfig, DEFAULT_CONFIG
from src.auction.models import PlayerCard, CannotFieldXIError


def assemble_xi(
    cards: list[PlayerCard],
    config: AuctionConfig = DEFAULT_CONFIG,
) -> tuple[list[str], list[str]]:
    """Pick and order the best legal XI from a drafted squad.

    Returns ``(batting_order_ids, bowler_ids)`` where ``batting_order_ids`` is
    exactly 11 ids (best batter first) and ``bowler_ids`` are the bowl-capable
    members of that XI (best bowler first).

    Raises :class:`CannotFieldXIError` if the squad has fewer than 11 players
    or no bowl-capable player at all (the engine requires ≥1 bowler).
    """
    if len(cards) < 11:
        raise CannotFieldXIError(
            f"Squad has {len(cards)} players; need at least 11 to field an XI."
        )

    by_overall = sorted(cards, key=lambda c: c.overall_rating, reverse=True)
    chosen: list[PlayerCard] = []
    chosen_ids: set[str] = set()

    def take(card: PlayerCard) -> None:
        if card.player_id not in chosen_ids and len(chosen) < 11:
            chosen.append(card)
            chosen_ids.add(card.player_id)

    # 1. Best keeper(s) first, up to the soft target.
    keepers = [c for c in by_overall if c.is_wicketkeeper]
    for c in keepers[: config.target_keepers]:
        take(c)

    # 2. Best bowl-capable players, up to the soft target.
    bowlers = [c for c in by_overall if c.can_bowl]
    for c in bowlers:
        if sum(1 for x in chosen if x.can_bowl) >= config.target_bowlers:
            break
        take(c)

    # 3. Fill the rest with the best remaining by overall rating.
    for c in by_overall:
        if len(chosen) >= 11:
            break
        take(c)

    # Guarantee the engine's one hard requirement: at least one bowler in the XI.
    if not any(c.can_bowl for c in chosen):
        spare_bowler = next((c for c in by_overall if c.can_bowl), None)
        if spare_bowler is None:
            raise CannotFieldXIError(
                "Squad has no bowl-capable player; cannot field a legal XI."
            )
        # Swap out the weakest non-bowler for the spare bowler.
        weakest = min(chosen, key=lambda c: c.overall_rating)
        chosen.remove(weakest)
        chosen.append(spare_bowler)

    batting_order = sorted(chosen, key=lambda c: c.bat_rating, reverse=True)
    bowler_xi = sorted(
        [c for c in chosen if c.can_bowl], key=lambda c: c.bowl_rating, reverse=True
    )
    return [c.player_id for c in batting_order], [c.player_id for c in bowler_xi]


def to_team_roster(
    team_id: str,
    name: str,
    squad: list[PlayerCard],
    config: AuctionConfig = DEFAULT_CONFIG,
    explicit_xi: list[str] | None = None,
) -> dict:
    """Build the ``TeamRoster`` dict ``simulate_season`` accepts.

    Shape: ``{"team_id", "name", "batting_order": [11 ids], "bowlers": [ids]}``.

    ``explicit_xi`` (11 player ids, in batting order) supports the manual-override
    screen: bowlers are derived as the bowl-capable members of that XI. All ids
    must belong to the drafted squad.
    """
    squad_ids = {c.player_id for c in squad}

    if explicit_xi is not None:
        if len(explicit_xi) != 11:
            raise CannotFieldXIError(
                f"Explicit XI must have exactly 11 players, got {len(explicit_xi)}."
            )
        if len(set(explicit_xi)) != 11:
            raise CannotFieldXIError("Explicit XI has duplicate players.")
        missing = [pid for pid in explicit_xi if pid not in squad_ids]
        if missing:
            raise CannotFieldXIError(
                f"Explicit XI references players not in the squad: {missing}."
            )
        by_id = {c.player_id: c for c in squad}
        bowlers = [pid for pid in explicit_xi if by_id[pid].can_bowl]
        if not bowlers:
            raise CannotFieldXIError("Explicit XI has no bowl-capable player.")
        batting_order = list(explicit_xi)
    else:
        batting_order, bowlers = assemble_xi(squad, config)

    return {
        "team_id": team_id,
        "name": name,
        "batting_order": batting_order,
        "bowlers": bowlers,
    }
