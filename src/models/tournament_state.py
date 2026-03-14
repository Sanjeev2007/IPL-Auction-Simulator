"""
Tournament-state data models for the IPL Auction Simulation System.

Defines the points table, tournament state, and aggregated simulation results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .team import Team
from .match_state import MatchResult


# ---------------------------------------------------------------------------
# Points table
# ---------------------------------------------------------------------------

@dataclass
class PointsTableEntry:
    """Single row in the league points table."""
    team: Team
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    no_results: int = 0
    points: int = 0                    # 2 per win
    nrr: float = 0.0                   # net run rate

    # internals for NRR calc
    runs_scored: int = 0
    overs_faced: float = 0.0           # decimal overs
    runs_conceded: int = 0
    overs_bowled: float = 0.0          # decimal overs

    @property
    def position(self) -> int:
        """Position is set externally after sorting."""
        return 0  # placeholder — set by tournament logic

    def update_nrr(self) -> None:
        """Recalculate NRR from cumulative runs/overs."""
        if self.overs_faced > 0 and self.overs_bowled > 0:
            self.nrr = (
                (self.runs_scored / self.overs_faced)
                - (self.runs_conceded / self.overs_bowled)
            )
        else:
            self.nrr = 0.0

    def __repr__(self) -> str:
        return (
            f"{self.team.team_id}: P={self.matches_played} W={self.wins} "
            f"L={self.losses} Pts={self.points} NRR={self.nrr:+.3f}"
        )


# ---------------------------------------------------------------------------
# Tournament state
# ---------------------------------------------------------------------------

@dataclass
class TournamentState:
    """State of a single IPL-style tournament simulation."""
    teams: list[Team] = field(default_factory=list)
    schedule: list[tuple[str, str]] = field(default_factory=list)
    # schedule stores (team_id_a, team_id_b) pairs

    results: list[MatchResult] = field(default_factory=list)
    points_table: list[PointsTableEntry] = field(default_factory=list)

    # Playoff results
    qualifier_1: Optional[MatchResult] = None
    eliminator: Optional[MatchResult] = None
    qualifier_2: Optional[MatchResult] = None
    final: Optional[MatchResult] = None

    champion: Optional[Team] = None

    @property
    def is_complete(self) -> bool:
        return self.champion is not None

    def sorted_table(self) -> list[PointsTableEntry]:
        """Return points table sorted by points (desc), then NRR (desc)."""
        return sorted(
            self.points_table,
            key=lambda e: (e.points, e.nrr),
            reverse=True,
        )


# ---------------------------------------------------------------------------
# Aggregated simulation results
# ---------------------------------------------------------------------------

@dataclass
class SimulationAggregates:
    """Results aggregated over N tournament simulations."""
    iterations: int = 0

    # Counts keyed by team_id
    win_counts: dict[str, int] = field(default_factory=dict)
    playoff_appearances: dict[str, int] = field(default_factory=dict)
    total_points: dict[str, int] = field(default_factory=dict)
    total_wins_league: dict[str, int] = field(default_factory=dict)

    # Derived (computed after all iterations)
    win_probability: dict[str, float] = field(default_factory=dict)
    avg_points: dict[str, float] = field(default_factory=dict)

    # Top performers across all iterations
    player_runs: dict[str, int] = field(default_factory=dict)      # player_id → total runs
    player_wickets: dict[str, int] = field(default_factory=dict)   # player_id → total wickets

    def compute_derived(self) -> None:
        """Calculate win probability and average points from raw counts."""
        if self.iterations == 0:
            return
        for team_id in self.win_counts:
            self.win_probability[team_id] = (
                self.win_counts[team_id] / self.iterations * 100
            )
        for team_id in self.total_points:
            self.avg_points[team_id] = (
                self.total_points[team_id] / self.iterations
            )

    def top_batters(self, n: int = 10) -> list[tuple[str, int]]:
        """Top N run-scorers across all simulations."""
        return sorted(
            self.player_runs.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:n]

    def top_bowlers(self, n: int = 10) -> list[tuple[str, int]]:
        """Top N wicket-takers across all simulations."""
        return sorted(
            self.player_wickets.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:n]
