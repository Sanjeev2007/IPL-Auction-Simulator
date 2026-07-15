"""Auction configuration — the knobs the owner tunes.

Money is stored throughout the auction in **paise-free INR** (whole rupees),
matching ``Base Price (INR)`` in ``players_master.csv``. Helpers here convert to
the crore/lakh notation used in messages and the UI.

Owner-confirmed defaults (2026-07): ₹100 cr budget, squad 11–15, 30 s per lot,
ascending open bids with tiered increments.
"""

from __future__ import annotations

from dataclasses import dataclass

# ── Currency units (INR) ────────────────────────────────────────────────────
LAKH = 100_000
CRORE = 100 * LAKH  # 10,000,000


def format_inr(amount: int) -> str:
    """Human-readable crore/lakh string, e.g. ``9_50_00_000`` → ``"9.5Cr"``."""
    if amount >= CRORE:
        v = amount / CRORE
        return f"{v:.2f}".rstrip("0").rstrip(".") + "Cr"
    v = amount / LAKH
    return f"{v:.2f}".rstrip("0").rstrip(".") + "L"


# ── Bid increment tiers ─────────────────────────────────────────────────────
# (threshold, increment): once the current bid reaches ``threshold``, the next
# raise steps by ``increment``. Ordered high→low; the first satisfied tier wins.
_INCREMENT_TIERS = (
    (5 * CRORE, 1 * CRORE),   # ≥ ₹5 cr  → +₹1 cr
    (1 * CRORE, 50 * LAKH),   # ≥ ₹1 cr  → +₹50 L
    (0, 25 * LAKH),           # <  ₹1 cr → +₹25 L
)


@dataclass(frozen=True)
class AuctionConfig:
    """Tunable rules for a single auction room."""

    starting_budget: int = 100 * CRORE     # ₹100 cr per participant
    squad_min: int = 11                    # min players to field a legal XI
    squad_max: int = 15                    # can't bid once squad is full
    timer_seconds: int = 30                # countdown per lot
    # Soft targets the auto-XI selector aims for (not hard bid-time rules).
    target_bowlers: int = 5                # prefer ≥5 bowl-capable in the XI
    target_keepers: int = 1                # prefer ≥1 wicketkeeper in the XI
    # Cap on how many players enter the lot queue (None = the whole catalog,
    # ordered by overall rating). Useful to keep a friendly game short.
    pool_size: int | None = None

    def increment_for(self, current_bid: int) -> int:
        """The minimum raise above ``current_bid`` for the next bid."""
        for threshold, inc in _INCREMENT_TIERS:
            if current_bid >= threshold:
                return inc
        return _INCREMENT_TIERS[-1][1]  # unreachable (threshold 0), kept for safety


DEFAULT_CONFIG = AuctionConfig()
