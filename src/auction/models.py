"""Auction domain models, enums, and errors.

These are transport-agnostic: no WebSocket, no FastAPI. The room state machine
in :mod:`src.auction.room` composes them; the WS layer only serializes them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ── Errors ──────────────────────────────────────────────────────────────────
class AuctionError(Exception):
    """Base class for every rule/validation failure in the auction.

    The WS layer catches these and emits an ``error`` message; anything *not*
    an ``AuctionError`` is a genuine bug and should surface loudly.
    """


class InvalidActionError(AuctionError):
    """Action attempted in the wrong room phase (e.g. bidding before start)."""


class UnknownParticipantError(AuctionError):
    """A participant id that isn't in this room."""


class NoActiveLotError(AuctionError):
    """No lot is currently up for bidding."""


class SquadFullError(AuctionError):
    """Participant already holds the maximum squad size."""


class BidTooLowError(AuctionError):
    """Bid is below ``current + increment`` (or below base for the first bid)."""


class InsufficientBudgetError(AuctionError):
    """Bid exceeds the participant's remaining budget."""


class AlreadyHighBidderError(AuctionError):
    """Participant is already the highest bidder — no self-outbidding."""


class CannotFieldXIError(AuctionError):
    """A drafted squad can't be reduced to a legal 11-man engine roster."""


# ── Enums ───────────────────────────────────────────────────────────────────
class LotStatus(str, Enum):
    PENDING = "pending"    # queued, not yet up
    ACTIVE = "active"      # currently being bid on
    SOLD = "sold"          # went to a bidder
    UNSOLD = "unsold"      # timer expired with no bids


class RoomPhase(str, Enum):
    LOBBY = "lobby"            # participants joining, not started
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


# ── Value objects ───────────────────────────────────────────────────────────
@dataclass
class PlayerCard:
    """Display + selection data for one player, snapshotted onto a lot.

    Carries exactly what the bidding UI shows and what the XI selector needs,
    so the room never has to reach back into the catalog mid-auction.
    """

    player_id: str
    name: str
    role: str                 # human role label, e.g. "All Rounders"
    country: str
    base_price: int
    bat_rating: float
    bowl_rating: float
    overall_rating: float
    can_bowl: bool
    is_wicketkeeper: bool

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "role": self.role,
            "country": self.country,
            "base_price": self.base_price,
            "bat_rating": self.bat_rating,
            "bowl_rating": self.bowl_rating,
            "overall_rating": self.overall_rating,
            "can_bowl": self.can_bowl,
            "is_wicketkeeper": self.is_wicketkeeper,
        }


@dataclass
class SquadEntry:
    """A player a participant won, and what they paid."""

    card: PlayerCard
    price: int

    def to_dict(self) -> dict:
        return {"player": self.card.to_dict(), "price": self.price}


@dataclass
class Participant:
    """One person in a room, with their budget and drafted squad."""

    id: str                          # public id (appears in rosters/broadcasts)
    display_name: str
    token: str                       # secret; the WS layer maps token → id
    is_host: bool = False
    budget_remaining: int = 0
    squad: list[SquadEntry] = field(default_factory=list)

    @property
    def squad_size(self) -> int:
        return len(self.squad)

    @property
    def spent(self) -> int:
        return sum(e.price for e in self.squad)

    def public_dict(self) -> dict:
        """Snapshot safe to broadcast to everyone (no token)."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "is_host": self.is_host,
            "budget_remaining": self.budget_remaining,
            "squad_size": self.squad_size,
            "squad": [e.to_dict() for e in self.squad],
        }


@dataclass
class Lot:
    """One player up (or queued) for auction."""

    index: int
    card: PlayerCard
    status: LotStatus = LotStatus.PENDING
    current_bid: int | None = None
    current_bidder_id: str | None = None
    sold_price: int | None = None
    winner_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "status": self.status.value,
            "player": self.card.to_dict(),
            "current_bid": self.current_bid,
            "current_bidder_id": self.current_bidder_id,
            "sold_price": self.sold_price,
            "winner_id": self.winner_id,
        }
