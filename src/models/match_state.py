"""
Match-state data models for the IPL Auction Simulation System.

Defines the per-ball, per-innings, and per-match data structures used
by the match simulation engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .player import Player
from .team import Team


# ---------------------------------------------------------------------------
# Ball-level
# ---------------------------------------------------------------------------

@dataclass
class BallOutcome:
    """Result of a single delivery."""
    runs: int                          # 0–6
    is_wicket: bool = False
    is_extra: bool = False             # wide or no-ball
    extra_type: Optional[str] = None   # "wide" | "no_ball" | None
    batter: Optional[Player] = None
    bowler: Optional[Player] = None
    over_number: int = 0               # 1-indexed
    ball_in_over: int = 0              # 1-indexed (1-6)
    commentary: str = ""               # optional text description


# ---------------------------------------------------------------------------
# Innings-level
# ---------------------------------------------------------------------------

@dataclass
class BatterScorecard:
    """Individual batter's innings stats."""
    player_id: str
    name: str
    runs: int = 0
    balls_faced: int = 0
    fours: int = 0
    sixes: int = 0
    is_out: bool = False
    dismissal_info: str = ""           # e.g. "c Kohli b Bumrah"

    @property
    def strike_rate(self) -> float:
        if self.balls_faced == 0:
            return 0.0
        return (self.runs / self.balls_faced) * 100


@dataclass
class BowlerFigures:
    """Individual bowler's match figures."""
    player_id: str
    name: str
    overs: float = 0.0                # e.g. 3.4 = 3 overs 4 balls
    maidens: int = 0
    runs_conceded: int = 0
    wickets: int = 0
    balls_bowled: int = 0

    @property
    def economy(self) -> float:
        overs_decimal = self.balls_bowled / 6
        if overs_decimal == 0:
            return 0.0
        return self.runs_conceded / overs_decimal


@dataclass
class InningsState:
    """
    Full state of one innings (1st or 2nd).

    The simulation engine mutates this object ball-by-ball.
    """
    batting_team: Team
    bowling_team: Team
    score: int = 0
    wickets: int = 0
    balls_bowled: int = 0              # 0-120
    balls_log: list[BallOutcome] = field(default_factory=list)
    target: Optional[int] = None      # set for 2nd innings

    # Scorecards keyed by player_id
    batter_scorecards: dict[str, BatterScorecard] = field(default_factory=dict)
    bowler_figures: dict[str, BowlerFigures] = field(default_factory=dict)

    # Current players at crease
    striker_id: Optional[str] = None
    non_striker_id: Optional[str] = None
    current_bowler_id: Optional[str] = None
    next_batter_index: int = 2         # next in batting order

    @property
    def overs_completed(self) -> float:
        """E.g. 14.3 means 14 overs and 3 balls."""
        full_overs = self.balls_bowled // 6
        remaining = self.balls_bowled % 6
        return full_overs + remaining / 10  # display format: 14.3

    @property
    def overs_decimal(self) -> float:
        """Decimal overs for NRR calc (14 overs 3 balls = 14.5)."""
        return self.balls_bowled / 6

    @property
    def phase(self) -> str:
        """Current match phase."""
        over = self.balls_bowled // 6
        if over < 6:
            return "powerplay"
        elif over < 16:
            return "middle"
        else:
            return "death"

    @property
    def is_complete(self) -> bool:
        """Innings is over if all out, all overs bowled, or target chased."""
        if self.wickets >= 10:
            return True
        if self.balls_bowled >= 120:
            return True
        if self.target is not None and self.score >= self.target:
            return True
        return False


# ---------------------------------------------------------------------------
# Match-level
# ---------------------------------------------------------------------------

@dataclass
class MatchResult:
    """Complete result of a simulated T20 match."""
    match_id: str
    team_1: Team
    team_2: Team
    innings_1: Optional[InningsState] = None
    innings_2: Optional[InningsState] = None
    winner: Optional[Team] = None
    margin: str = ""                   # e.g. "5 wickets" or "23 runs"
    player_of_match: Optional[Player] = None

    @property
    def team_1_score(self) -> str:
        if self.innings_1:
            return f"{self.innings_1.score}/{self.innings_1.wickets}"
        return "—"

    @property
    def team_2_score(self) -> str:
        if self.innings_2:
            return f"{self.innings_2.score}/{self.innings_2.wickets}"
        return "—"

    def summary(self) -> str:
        if self.winner:
            return (
                f"{self.team_1.name} {self.team_1_score} vs "
                f"{self.team_2.name} {self.team_2_score} — "
                f"{self.winner.name} won by {self.margin}"
            )
        return "Match result not available"
