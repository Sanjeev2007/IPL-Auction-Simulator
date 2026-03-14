"""
Team data model for the IPL Auction Simulation System.

A Team holds a full squad and can select a playing XI, batting order,
and bowling plan for match simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .player import Player, Role


@dataclass
class Team:
    """Represents an IPL franchise with its full squad and match-day selections."""

    team_id: str                                  # e.g. "CSK"
    name: str                                     # e.g. "Chennai Super Kings"
    players: list[Player] = field(default_factory=list)  # full squad

    # ── Match-day selections (set before simulation) ─────────────────────
    playing_xi: list[Player] = field(default_factory=list)
    batting_order: list[Player] = field(default_factory=list)
    bowling_plan: list[tuple[Player, int]] = field(default_factory=list)
    # bowling_plan: list of (bowler, max_overs_to_bowl)

    # ── Computed team metrics (set by rating engine) ─────────────────────
    batting_strength: float = 0.0
    bowling_strength: float = 0.0
    team_rating: float = 0.0

    # ── Helpers ──────────────────────────────────────────────────────────

    @property
    def squad_size(self) -> int:
        return len(self.players)

    def batters(self) -> list[Player]:
        """Return all players who can bat (typically all 11)."""
        return [p for p in self.playing_xi if p.can_bat]

    def bowlers(self) -> list[Player]:
        """Return all players eligible to bowl."""
        return [p for p in self.playing_xi if p.can_bowl]

    def by_role(self, role: Role) -> list[Player]:
        """Filter squad by role."""
        return [p for p in self.players if p.role == role]

    def __repr__(self) -> str:
        return f"Team(id={self.team_id!r}, name={self.name!r}, squad={self.squad_size})"
