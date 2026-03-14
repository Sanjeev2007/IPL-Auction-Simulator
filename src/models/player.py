"""
Player data model for the IPL Auction Simulation System.

Defines the Player dataclass and supporting enums (Role, BattingStyle, BowlingStyle).
Players carry both raw stats and computed ratings/probabilities used by the simulation engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Role(Enum):
    """Primary playing role."""
    BATTER = "Batsmen"
    BOWLER_FAST = "Fast Bowlers"
    BOWLER_SPIN = "Spinners"
    ALL_ROUNDER = "All Rounders"
    WICKETKEEPER = "Wicketkeepers"

    @classmethod
    def from_csv(cls, raw: str) -> "Role":
        """Parse a role string from the CSV into a Role enum."""
        mapping = {
            "batsmen": cls.BATTER,
            "fast bowlers": cls.BOWLER_FAST,
            "spinners": cls.BOWLER_SPIN,
            "all rounders": cls.ALL_ROUNDER,
            "wicketkeepers": cls.WICKETKEEPER,
        }
        key = raw.strip().lower()
        if key not in mapping:
            raise ValueError(f"Unknown role: '{raw}'. Expected one of {list(mapping.keys())}")
        return mapping[key]


class BattingStyle(Enum):
    RIGHT = "Right"
    LEFT = "Left"
    UNKNOWN = "Unknown"


class BowlingStyle(Enum):
    RIGHT_ARM_FAST = "Right-arm Fast"
    LEFT_ARM_FAST = "Left-arm Fast"
    RIGHT_ARM_SPIN = "Right-arm Spin"
    LEFT_ARM_SPIN = "Left-arm Spin"
    RIGHT_ARM_MEDIUM = "Right-arm Medium"
    LEFT_ARM_MEDIUM = "Left-arm Medium"
    NONE = "None"
    UNKNOWN = "Unknown"


# ---------------------------------------------------------------------------
# Player dataclass
# ---------------------------------------------------------------------------

@dataclass
class Player:
    """
    Represents a single player in the auction pool.

    Fields are grouped into:
      - Identity  (always present after dataset_builder)
      - Ratings   (populated after rating_model runs)
      - Phase stats (populated after enrichment)
      - Probabilities (populated after probability_mapper)
      - Context   (populated after news_sentiment)
    """

    # ── Identity ──────────────────────────────────────────────────────────
    player_id: str                          # e.g. "BAT001"
    name: str                               # e.g. "Virat Kohli"
    role: Role
    base_price: int                         # in INR  (e.g. 20_000_000)
    country: str = "Unknown"
    batting_style: BattingStyle = BattingStyle.UNKNOWN
    bowling_style: BowlingStyle = BowlingStyle.UNKNOWN

    # ── Ratings (Phase 3) ────────────────────────────────────────────────
    bat_rating: float = 0.0                 # 0-100
    bowl_rating: float = 0.0               # 0-100
    allround_value: float = 0.0            # 0-100
    popularity_score: float = 0.0          # 0-100
    overall_rating: float = 0.0            # 0-100

    # ── Phase-specific stats (Phase 2) ───────────────────────────────────
    powerplay_sr: float = 0.0              # batting SR overs 1-6
    middle_sr: float = 0.0                 # batting SR overs 7-15
    death_sr: float = 0.0                  # batting SR overs 16-20
    powerplay_econ: float = 0.0            # bowling economy overs 1-6
    middle_econ: float = 0.0               # bowling economy overs 7-15
    death_econ: float = 0.0                # bowling economy overs 16-20

    # ── Ball outcome probabilities (Phase 3) ─────────────────────────────
    # {phase: {outcome: probability}}  — populated by probability_mapper
    batting_probs: dict = field(default_factory=dict)
    bowling_probs: dict = field(default_factory=dict)

    # ── Context (Phase 2) ────────────────────────────────────────────────
    injury_risk: str = "Low"               # "Low" | "Medium" | "High"
    sentiment_score: float = 50.0          # 0-100
    news_summary: str = ""

    # ── Helpers ──────────────────────────────────────────────────────────

    @property
    def is_batter(self) -> bool:
        return self.role in (Role.BATTER, Role.WICKETKEEPER)

    @property
    def is_bowler(self) -> bool:
        return self.role in (Role.BOWLER_FAST, Role.BOWLER_SPIN)

    @property
    def is_allrounder(self) -> bool:
        return self.role == Role.ALL_ROUNDER

    @property
    def can_bat(self) -> bool:
        return True  # everyone bats in T20

    @property
    def can_bowl(self) -> bool:
        return self.role in (Role.BOWLER_FAST, Role.BOWLER_SPIN, Role.ALL_ROUNDER)

    def base_price_display(self) -> str:
        """Human-readable price string."""
        if self.base_price >= 10_000_000:
            return f"{self.base_price / 10_000_000:.1f}Cr"
        return f"{self.base_price / 100_000:.0f}L"

    def __repr__(self) -> str:
        return (
            f"Player(id={self.player_id!r}, name={self.name!r}, "
            f"role={self.role.name}, price={self.base_price_display()})"
        )
