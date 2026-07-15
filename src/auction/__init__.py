"""Live multiplayer auction (Milestone 5).

Phase 1 (this module) is the *backend core*: rooms, participants, a bidding
state machine, and the rules the server must enforce — all pure Python with no
transport concerns. The WebSocket layer (phase 2) drives this state machine and
broadcasts the event dicts it returns; it does not re-implement any rules here.

The auction's output is a set of drafted squads, which
:mod:`src.auction.roster` turns into engine-ready ``TeamRoster`` dicts that feed
straight into ``POST /api/simulate_season``.
"""

from .config import AuctionConfig, DEFAULT_CONFIG, CRORE, LAKH
from .models import (
    AuctionError,
    BidTooLowError,
    InsufficientBudgetError,
    SquadFullError,
    AlreadyHighBidderError,
    UnknownParticipantError,
    NoActiveLotError,
    InvalidActionError,
    CannotFieldXIError,
    LotStatus,
    RoomPhase,
    Participant,
    Lot,
    PlayerCard,
)
from .catalog import CatalogEntry, catalog_from_players, load_catalog
from .roster import assemble_xi, to_team_roster
from .room import AuctionRoom
from .manager import AuctionManager

__all__ = [
    "AuctionConfig",
    "DEFAULT_CONFIG",
    "CRORE",
    "LAKH",
    "AuctionError",
    "BidTooLowError",
    "InsufficientBudgetError",
    "SquadFullError",
    "AlreadyHighBidderError",
    "UnknownParticipantError",
    "NoActiveLotError",
    "InvalidActionError",
    "CannotFieldXIError",
    "LotStatus",
    "RoomPhase",
    "Participant",
    "Lot",
    "PlayerCard",
    "CatalogEntry",
    "catalog_from_players",
    "load_catalog",
    "assemble_xi",
    "to_team_roster",
    "AuctionRoom",
    "AuctionManager",
]
