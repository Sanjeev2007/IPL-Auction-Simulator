"""The auction room state machine.

One :class:`AuctionRoom` owns a lobby of participants, a queue of lots, and the
bidding rules the server enforces. It is deliberately **timer-agnostic**: the
countdown lives in the WS layer (phase 2), which calls :meth:`resolve_active_lot`
when the timer for a lot expires. Every mutating method returns a plain event
dict whose ``type`` matches the WS protocol, so the transport layer only has to
broadcast — never re-derive — state.

All rule violations raise :class:`AuctionError` subclasses; the caller turns
those into ``error`` messages.
"""

from __future__ import annotations

import secrets

from src.auction.config import AuctionConfig, DEFAULT_CONFIG, format_inr
from src.auction.catalog import CatalogEntry
from src.auction.models import (
    AlreadyHighBidderError,
    BidTooLowError,
    CannotFieldXIError,
    InsufficientBudgetError,
    InvalidActionError,
    Lot,
    LotStatus,
    NoActiveLotError,
    Participant,
    RoomPhase,
    SquadEntry,
    SquadFullError,
    UnknownParticipantError,
)
from src.auction.roster import to_team_roster

_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no easily-confused chars


class AuctionRoom:
    """A single live auction: lobby → bidding → complete."""

    def __init__(
        self,
        catalog: dict[str, CatalogEntry],
        config: AuctionConfig = DEFAULT_CONFIG,
        code: str | None = None,
    ):
        self.code = code or self._gen_code()
        self.config = config
        self.host_token = secrets.token_urlsafe(16)
        self.catalog = catalog

        self.phase: RoomPhase = RoomPhase.LOBBY
        self.participants: dict[str, Participant] = {}
        self.lots: list[Lot] = []
        self.current_index: int = -1
        self.bid_log: list[dict] = []
        self._pcount = 0

    # ── construction helpers ────────────────────────────────────────────────
    @staticmethod
    def _gen_code(length: int = 5) -> str:
        return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))

    def _new_participant_id(self) -> str:
        self._pcount += 1
        return f"P{self._pcount}"

    # ── lobby ────────────────────────────────────────────────────────────────
    def add_participant(self, display_name: str, is_host: bool = False) -> Participant:
        """Add someone to the lobby. Only allowed before the auction starts."""
        if self.phase is not RoomPhase.LOBBY:
            raise InvalidActionError("Cannot join after the auction has started.")
        name = display_name.strip()
        if not name:
            raise InvalidActionError("Display name is required.")
        p = Participant(
            id=self._new_participant_id(),
            display_name=name,
            token=secrets.token_urlsafe(12),
            is_host=is_host,
            budget_remaining=self.config.starting_budget,
        )
        self.participants[p.id] = p
        return p

    def get_participant(self, participant_id: str) -> Participant:
        p = self.participants.get(participant_id)
        if p is None:
            raise UnknownParticipantError(f"No participant {participant_id!r} in room.")
        return p

    # ── start ────────────────────────────────────────────────────────────────
    def start(self, host_token: str, player_ids: list[str] | None = None) -> dict:
        """Begin the auction: build the lot queue and open the first lot.

        ``player_ids`` overrides which players go up (order preserved); by
        default the whole catalog is used, ordered by overall rating desc and
        capped at ``config.pool_size``.
        """
        if host_token != self.host_token:
            raise InvalidActionError("Only the host can start the auction.")
        if self.phase is not RoomPhase.LOBBY:
            raise InvalidActionError("Auction has already started.")
        if len(self.participants) < 2:
            raise InvalidActionError("Need at least 2 participants to start.")

        if player_ids is None:
            entries = sorted(
                self.catalog.values(), key=lambda e: e.overall_rating, reverse=True
            )
            if self.config.pool_size is not None:
                entries = entries[: self.config.pool_size]
        else:
            missing = [pid for pid in player_ids if pid not in self.catalog]
            if missing:
                raise InvalidActionError(f"Unknown players in pool: {missing}.")
            entries = [self.catalog[pid] for pid in player_ids]

        if not entries:
            raise InvalidActionError("Player pool is empty.")

        self.lots = [Lot(index=i, card=e.to_card()) for i, e in enumerate(entries)]
        self.phase = RoomPhase.IN_PROGRESS
        self.current_index = 0
        self.lots[0].status = LotStatus.ACTIVE
        return {"type": "lot_update", "lot": self.active_lot.to_dict(),
                "min_next_bid": self.min_next_bid()}

    # ── active-lot accessors ─────────────────────────────────────────────────
    @property
    def active_lot(self) -> Lot | None:
        if self.phase is not RoomPhase.IN_PROGRESS:
            return None
        if not (0 <= self.current_index < len(self.lots)):
            return None
        lot = self.lots[self.current_index]
        return lot if lot.status is LotStatus.ACTIVE else None

    def min_next_bid(self) -> int | None:
        """The smallest legal next bid on the active lot (``None`` if none)."""
        lot = self.active_lot
        if lot is None:
            return None
        if lot.current_bid is None:
            return lot.card.base_price
        return lot.current_bid + self.config.increment_for(lot.current_bid)

    # ── bidding ──────────────────────────────────────────────────────────────
    def place_bid(self, participant_id: str, amount: int) -> dict:
        """Record a bid, enforcing every server-side rule.

        Rules: an auction must be live with an active lot; the bidder must be a
        known participant whose squad isn't full and who isn't already the high
        bidder; the amount must be ≥ the minimum next bid and ≤ their budget.
        """
        lot = self.active_lot
        if lot is None:
            raise NoActiveLotError("No lot is currently up for bidding.")

        p = self.get_participant(participant_id)

        if p.squad_size >= self.config.squad_max:
            raise SquadFullError(
                f"Squad is full ({self.config.squad_max} players); cannot bid."
            )
        if lot.current_bidder_id == p.id:
            raise AlreadyHighBidderError("You are already the highest bidder.")

        min_next = self.min_next_bid()
        if amount < min_next:
            raise BidTooLowError(
                f"Bid must be at least {format_inr(min_next)} "
                f"(you bid {format_inr(amount)})."
            )
        if amount > p.budget_remaining:
            raise InsufficientBudgetError(
                f"Bid {format_inr(amount)} exceeds your budget "
                f"{format_inr(p.budget_remaining)}."
            )

        lot.current_bid = amount
        lot.current_bidder_id = p.id
        event = {
            "type": "bid_placed",
            "lot_index": lot.index,
            "player_id": lot.card.player_id,
            "bidder_id": p.id,
            "bidder_name": p.display_name,
            "amount": amount,
            "amount_display": format_inr(amount),
            "min_next_bid": self.min_next_bid(),
        }
        self.bid_log.append(event)
        return event

    # ── lot resolution (driven by the WS timer) ──────────────────────────────
    def resolve_active_lot(self) -> dict:
        """Close the active lot (timer expired): SOLD to the leader, or UNSOLD.

        On a sale the winner's budget is deducted and the player joins their
        squad. Then the queue advances; if it's exhausted — or every squad is
        full — the auction completes.
        """
        lot = self.active_lot
        if lot is None:
            raise NoActiveLotError("No active lot to resolve.")

        if lot.current_bidder_id is not None:
            winner = self.participants[lot.current_bidder_id]
            price = lot.current_bid
            lot.status = LotStatus.SOLD
            lot.sold_price = price
            lot.winner_id = winner.id
            winner.budget_remaining -= price
            winner.squad.append(SquadEntry(card=lot.card, price=price))
            resolution = {
                "type": "lot_sold",
                "lot_index": lot.index,
                "player_id": lot.card.player_id,
                "player_name": lot.card.name,
                "winner_id": winner.id,
                "winner_name": winner.display_name,
                "price": price,
                "price_display": format_inr(price),
                "winner_budget_remaining": winner.budget_remaining,
            }
        else:
            lot.status = LotStatus.UNSOLD
            resolution = {
                "type": "lot_unsold",
                "lot_index": lot.index,
                "player_id": lot.card.player_id,
                "player_name": lot.card.name,
            }

        self._advance()
        resolution["auction_complete"] = self.phase is RoomPhase.COMPLETE
        if self.active_lot is not None:
            resolution["next_lot"] = self.active_lot.to_dict()
            resolution["min_next_bid"] = self.min_next_bid()
        else:
            resolution["next_lot"] = None
        return resolution

    def _advance(self) -> None:
        """Move to the next lot, or finish the auction."""
        # Everyone maxed out → nothing left to buy.
        if self.participants and all(
            p.squad_size >= self.config.squad_max for p in self.participants.values()
        ):
            self.current_index = len(self.lots)
            self.phase = RoomPhase.COMPLETE
            return

        self.current_index += 1
        if self.current_index >= len(self.lots):
            self.phase = RoomPhase.COMPLETE
            return
        self.lots[self.current_index].status = LotStatus.ACTIVE

    # ── handoff to the simulation engine ─────────────────────────────────────
    def assemble_rosters(
        self, overrides: dict[str, list[str]] | None = None
    ) -> dict:
        """Reduce every eligible squad to an engine ``TeamRoster``.

        Participants whose squad is below ``squad_min`` can't field an XI and
        are reported under ``"skipped"`` rather than failing the whole batch.
        ``overrides`` maps a participant id to an explicit 11-man XI (the
        manual-override screen).

        Returns ``{"rosters": [...], "skipped": [...]}``. ``rosters`` is exactly
        what ``POST /api/simulate_season`` accepts as ``teams``.
        """
        overrides = overrides or {}
        rosters: list[dict] = []
        skipped: list[dict] = []
        for p in self.participants.values():
            if p.squad_size < self.config.squad_min:
                skipped.append({
                    "participant_id": p.id,
                    "name": p.display_name,
                    "squad_size": p.squad_size,
                    "reason": f"squad below minimum ({self.config.squad_min})",
                })
                continue
            cards = [e.card for e in p.squad]
            try:
                roster = to_team_roster(
                    team_id=p.id,
                    name=p.display_name,
                    squad=cards,
                    config=self.config,
                    explicit_xi=overrides.get(p.id),
                )
            except CannotFieldXIError as e:
                skipped.append({
                    "participant_id": p.id,
                    "name": p.display_name,
                    "squad_size": p.squad_size,
                    "reason": str(e),
                })
                continue
            rosters.append(roster)
        return {"rosters": rosters, "skipped": skipped}

    # ── serialization ────────────────────────────────────────────────────────
    def state(self) -> dict:
        """Full room snapshot for a ``room_state`` broadcast."""
        return {
            "type": "room_state",
            "code": self.code,
            "phase": self.phase.value,
            "config": {
                "starting_budget": self.config.starting_budget,
                "squad_min": self.config.squad_min,
                "squad_max": self.config.squad_max,
                "timer_seconds": self.config.timer_seconds,
            },
            "participants": [p.public_dict() for p in self.participants.values()],
            "active_lot": self.active_lot.to_dict() if self.active_lot else None,
            "min_next_bid": self.min_next_bid(),
            "lots_total": len(self.lots),
            "lots_remaining": max(0, len(self.lots) - self.current_index - 1)
            if self.phase is RoomPhase.IN_PROGRESS else 0,
            "bid_log": self.bid_log[-25:],
        }
