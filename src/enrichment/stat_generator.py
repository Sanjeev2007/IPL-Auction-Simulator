"""
⚠️  DEPRECATED — SYNTHETIC (md5-seeded) STAT GENERATOR. NOT REAL DATA. ⚠️

This module fabricates plausible-looking T20 statistics by md5-hashing the
Player_ID and varying canned per-role/per-tier templates. None of it is real.
In particular ``generate_news_sentiment`` produced the fake "real-time news
sentiment" the README once advertised — that headline feature is RETIRED.

The default pipeline (``scripts/run_real_enrichment.py``) no longer imports or
calls anything in this file; it derives every number from real Cricsheet
ball-by-ball data. This module is retained only for the legacy
``scripts/run_enrichment.py`` demo path and must never be presented as, or
relabelled into, real or real-time data.

Generates statistics based on:
  - Player role (Batter / WK / All-rounder / Fast Bowler / Spinner)
  - Base price tier (2Cr / 1.5Cr / 1Cr / 50L)
  - Deterministic md5 seeding from Player_ID for reproducibility
"""

from __future__ import annotations

import hashlib
import math


def _seed_from_id(player_id: str) -> float:
    """Deterministic pseudo-random float [0,1) from a player ID."""
    h = hashlib.md5(player_id.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _vary(base: float, seed: float, spread: float = 0.15) -> float:
    """Apply ±spread variation to a base value using the seed."""
    factor = 1.0 + (seed - 0.5) * 2 * spread
    return round(base * factor, 1)


def _vary_int(base: float, seed: float, spread: float = 0.15) -> int:
    return max(0, int(round(_vary(base, seed, spread))))


# ---------------------------------------------------------------------------
# Price tier mapping (INR → tier label)
# ---------------------------------------------------------------------------

def price_tier(base_price: int) -> str:
    if base_price >= 20_000_000:
        return "elite"       # 2Cr
    elif base_price >= 15_000_000:
        return "premium"     # 1.5Cr
    elif base_price >= 10_000_000:
        return "standard"    # 1Cr
    else:
        return "budget"      # 50L


# ---------------------------------------------------------------------------
# IPL stat profiles by role × tier
# ---------------------------------------------------------------------------

# Base templates: {stat: value}
# Actual values will be varied using the seed

_IPL_PROFILES = {
    # ── BATSMEN ──────────────────────────────────────────────────────────
    ("Batsmen", "elite"): {
        "matches": 60, "runs": 1800, "batting_average": 34.0, "strike_rate": 142.0,
        "fifties": 12, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 145.0, "middle_sr": 138.0, "death_sr": 152.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    ("Batsmen", "premium"): {
        "matches": 45, "runs": 1200, "batting_average": 29.0, "strike_rate": 135.0,
        "fifties": 7, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 138.0, "middle_sr": 132.0, "death_sr": 145.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    ("Batsmen", "standard"): {
        "matches": 32, "runs": 750, "batting_average": 25.0, "strike_rate": 128.0,
        "fifties": 4, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 130.0, "middle_sr": 125.0, "death_sr": 138.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    ("Batsmen", "budget"): {
        "matches": 15, "runs": 280, "batting_average": 20.0, "strike_rate": 122.0,
        "fifties": 1, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 125.0, "middle_sr": 118.0, "death_sr": 130.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },

    # ── WICKETKEEPERS ────────────────────────────────────────────────────
    ("Wicketkeepers", "elite"): {
        "matches": 58, "runs": 1700, "batting_average": 33.0, "strike_rate": 140.0,
        "fifties": 11, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 142.0, "middle_sr": 136.0, "death_sr": 155.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    ("Wicketkeepers", "premium"): {
        "matches": 42, "runs": 1050, "batting_average": 28.0, "strike_rate": 135.0,
        "fifties": 6, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 138.0, "middle_sr": 130.0, "death_sr": 148.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    ("Wicketkeepers", "standard"): {
        "matches": 28, "runs": 550, "batting_average": 22.0, "strike_rate": 125.0,
        "fifties": 3, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 128.0, "middle_sr": 122.0, "death_sr": 135.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    ("Wicketkeepers", "budget"): {
        "matches": 12, "runs": 200, "batting_average": 18.0, "strike_rate": 118.0,
        "fifties": 1, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 120.0, "middle_sr": 115.0, "death_sr": 125.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },

    # ── ALL ROUNDERS ─────────────────────────────────────────────────────
    ("All Rounders", "elite"): {
        "matches": 55, "runs": 1100, "batting_average": 27.0, "strike_rate": 145.0,
        "fifties": 5, "hundreds": 0, "wickets": 38, "economy": 8.2, "bowling_strike_rate": 21.0,
        "powerplay_sr": 135.0, "middle_sr": 142.0, "death_sr": 162.0,
        "powerplay_econ": 7.8, "middle_econ": 8.0, "death_econ": 9.5,
    },
    ("All Rounders", "premium"): {
        "matches": 42, "runs": 750, "batting_average": 23.0, "strike_rate": 135.0,
        "fifties": 3, "hundreds": 0, "wickets": 28, "economy": 8.0, "bowling_strike_rate": 22.0,
        "powerplay_sr": 128.0, "middle_sr": 132.0, "death_sr": 148.0,
        "powerplay_econ": 7.5, "middle_econ": 7.8, "death_econ": 9.0,
    },
    ("All Rounders", "standard"): {
        "matches": 30, "runs": 450, "batting_average": 20.0, "strike_rate": 128.0,
        "fifties": 2, "hundreds": 0, "wickets": 18, "economy": 8.5, "bowling_strike_rate": 24.0,
        "powerplay_sr": 122.0, "middle_sr": 125.0, "death_sr": 140.0,
        "powerplay_econ": 8.0, "middle_econ": 8.2, "death_econ": 9.8,
    },
    ("All Rounders", "budget"): {
        "matches": 12, "runs": 180, "batting_average": 16.0, "strike_rate": 120.0,
        "fifties": 0, "hundreds": 0, "wickets": 8, "economy": 9.0, "bowling_strike_rate": 26.0,
        "powerplay_sr": 115.0, "middle_sr": 118.0, "death_sr": 130.0,
        "powerplay_econ": 8.5, "middle_econ": 8.8, "death_econ": 10.5,
    },

    # ── FAST BOWLERS ─────────────────────────────────────────────────────
    ("Fast Bowlers", "elite"): {
        "matches": 52, "runs": 40, "batting_average": 6.0, "strike_rate": 95.0,
        "fifties": 0, "hundreds": 0, "wickets": 62, "economy": 8.0, "bowling_strike_rate": 17.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.2, "middle_econ": 7.8, "death_econ": 9.5,
    },
    ("Fast Bowlers", "premium"): {
        "matches": 40, "runs": 30, "batting_average": 5.0, "strike_rate": 85.0,
        "fifties": 0, "hundreds": 0, "wickets": 42, "economy": 8.5, "bowling_strike_rate": 19.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.8, "middle_econ": 8.2, "death_econ": 10.0,
    },
    ("Fast Bowlers", "standard"): {
        "matches": 28, "runs": 20, "batting_average": 4.0, "strike_rate": 78.0,
        "fifties": 0, "hundreds": 0, "wickets": 28, "economy": 9.0, "bowling_strike_rate": 21.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 8.2, "middle_econ": 8.8, "death_econ": 10.5,
    },
    ("Fast Bowlers", "budget"): {
        "matches": 10, "runs": 8, "batting_average": 3.0, "strike_rate": 70.0,
        "fifties": 0, "hundreds": 0, "wickets": 10, "economy": 9.5, "bowling_strike_rate": 24.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 8.8, "middle_econ": 9.2, "death_econ": 11.0,
    },

    # ── SPINNERS ─────────────────────────────────────────────────────────
    ("Spinners", "elite"): {
        "matches": 52, "runs": 60, "batting_average": 6.0, "strike_rate": 85.0,
        "fifties": 0, "hundreds": 0, "wickets": 58, "economy": 7.0, "bowling_strike_rate": 17.5,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.2, "middle_econ": 6.5, "death_econ": 7.8,
    },
    ("Spinners", "premium"): {
        "matches": 38, "runs": 40, "batting_average": 5.0, "strike_rate": 75.0,
        "fifties": 0, "hundreds": 0, "wickets": 38, "economy": 7.5, "bowling_strike_rate": 19.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.5, "middle_econ": 7.0, "death_econ": 8.2,
    },
    ("Spinners", "standard"): {
        "matches": 25, "runs": 25, "batting_average": 4.0, "strike_rate": 70.0,
        "fifties": 0, "hundreds": 0, "wickets": 24, "economy": 8.0, "bowling_strike_rate": 21.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 8.0, "middle_econ": 7.5, "death_econ": 8.8,
    },
    ("Spinners", "budget"): {
        "matches": 10, "runs": 10, "batting_average": 3.0, "strike_rate": 60.0,
        "fifties": 0, "hundreds": 0, "wickets": 10, "economy": 8.5, "bowling_strike_rate": 23.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 8.5, "middle_econ": 8.0, "death_econ": 9.5,
    },
}


def generate_ipl_stats(player_id: str, role: str, base_price: int) -> dict:
    """Generate a complete IPL 5-year stats dict for a player."""
    tier = price_tier(base_price)
    profile = _IPL_PROFILES.get((role, tier))
    if profile is None:
        # Fallback: use standard tier for the role
        profile = _IPL_PROFILES.get((role, "standard"), _IPL_PROFILES[("Batsmen", "standard")])

    seed = _seed_from_id(player_id)
    # Use different seed offsets for different stats to avoid correlation
    stats = {}
    for i, (key, val) in enumerate(profile.items()):
        s = (seed + i * 0.07) % 1.0
        if isinstance(val, int) or (isinstance(val, float) and val == int(val) and key in ("matches", "runs", "fifties", "hundreds", "wickets")):
            stats[key] = _vary_int(val, s, 0.20)
        else:
            stats[key] = round(_vary(val, s, 0.12), 1)
    return stats


# ---------------------------------------------------------------------------
# Other T20 League profiles
# ---------------------------------------------------------------------------

_LEAGUES_BY_ROLE = {
    "Batsmen": ["International T20"],
    "Wicketkeepers": ["International T20"],
    "All Rounders": ["International T20"],
    "Fast Bowlers": ["International T20"],
    "Spinners": ["International T20"],
}

# Some roles tend to play in more leagues
_EXTRA_LEAGUES = [
    "Big Bash League", "Caribbean Premier League", "Pakistan Super League",
    "SA20", "ILT20", "Vitality Blast",
]


def generate_t20_stats(player_id: str, role: str, base_price: int) -> list[dict]:
    """Generate other T20 league stats for a player. Returns list of league entries."""
    tier = price_tier(base_price)
    seed = _seed_from_id(player_id)

    entries = []

    # Everyone gets International T20
    int_entry = _generate_single_league_stat(player_id, role, tier, "International T20", seed)
    entries.append(int_entry)

    # Higher-tier players may play in additional leagues
    if tier == "elite":
        num_extra = 1 + int(seed * 2.5)  # 1-3 extra leagues
    elif tier == "premium":
        num_extra = int(seed * 2)  # 0-1 extra
    elif tier == "standard":
        num_extra = int(seed * 1.5)  # 0-1 extra
    else:
        num_extra = 0

    for i in range(min(num_extra, len(_EXTRA_LEAGUES))):
        league = _EXTRA_LEAGUES[int((seed * 100 + i * 17) % len(_EXTRA_LEAGUES))]
        s2 = (seed + 0.3 * (i + 1)) % 1.0
        entry = _generate_single_league_stat(player_id, role, tier, league, s2)
        entries.append(entry)

    return entries


def _generate_single_league_stat(player_id: str, role: str, tier: str, league: str, seed: float) -> dict:
    """Generate stats for a single league."""
    is_bat = role in ("Batsmen", "Wicketkeepers")
    is_bowl = role in ("Fast Bowlers", "Spinners")
    is_ar = role == "All Rounders"

    # Match counts by tier
    match_base = {"elite": 40, "premium": 28, "standard": 18, "budget": 8}[tier]
    matches = _vary_int(match_base, seed, 0.25)

    if is_bat:
        runs = _vary_int(matches * 28, seed, 0.20)
        avg = round(_vary(28.0, seed, 0.18), 1)
        sr = round(_vary(135.0, seed, 0.10), 1)
        wickets = 0
        economy = 0.0
    elif is_bowl:
        runs = _vary_int(matches * 2, seed, 0.30)
        avg = round(_vary(5.0, seed, 0.25), 1)
        sr = round(_vary(75.0, seed, 0.15), 1)
        wickets = _vary_int(matches * 1.1, seed, 0.20)
        economy = round(_vary(7.5 if role == "Spinners" else 8.0, seed, 0.10), 1)
    else:  # all-rounder
        runs = _vary_int(matches * 20, seed, 0.20)
        avg = round(_vary(24.0, seed, 0.18), 1)
        sr = round(_vary(132.0, seed, 0.10), 1)
        wickets = _vary_int(matches * 0.7, seed, 0.25)
        economy = round(_vary(8.0, seed, 0.10), 1)

    return {
        "league": league,
        "matches": max(1, matches),
        "runs": max(0, runs),
        "batting_average": max(1.0, avg),
        "strike_rate": max(50.0, sr),
        "wickets": max(0, wickets),
        "economy": max(0, economy),
    }


# ---------------------------------------------------------------------------
# Recent form (12 months)
# ---------------------------------------------------------------------------

def generate_recent_form(player_id: str, role: str, base_price: int) -> dict:
    """Generate last-12-month performance stats."""
    tier = price_tier(base_price)
    seed = _seed_from_id(player_id + "_recent")

    is_bat = role in ("Batsmen", "Wicketkeepers")
    is_bowl = role in ("Fast Bowlers", "Spinners")

    match_base = {"elite": 18, "premium": 14, "standard": 10, "budget": 6}[tier]
    matches = max(1, _vary_int(match_base, seed, 0.25))

    if is_bat:
        runs = _vary_int(matches * 30, seed, 0.22)
        avg = round(_vary(30.0, seed, 0.18), 1)
        sr = round(_vary(138.0, seed, 0.10), 1)
        wickets = 0
        econ = 0.0
    elif is_bowl:
        runs = _vary_int(matches * 3, seed, 0.30)
        avg = round(_vary(6.0, seed, 0.25), 1)
        sr = round(_vary(78.0, seed, 0.15), 1)
        wickets = _vary_int(matches * 1.2, seed, 0.22)
        econ = round(_vary(7.5 if role == "Spinners" else 8.2, seed, 0.10), 1)
    else:  # all-rounder
        runs = _vary_int(matches * 22, seed, 0.20)
        avg = round(_vary(25.0, seed, 0.18), 1)
        sr = round(_vary(135.0, seed, 0.10), 1)
        wickets = _vary_int(matches * 0.8, seed, 0.25)
        econ = round(_vary(8.0, seed, 0.10), 1)

    return {
        "matches_12m": matches,
        "runs_12m": max(0, runs),
        "avg_12m": max(1.0, avg),
        "sr_12m": max(50.0, sr),
        "wickets_12m": max(0, wickets),
        "econ_12m": max(0, econ),
    }


# ---------------------------------------------------------------------------
# News / Sentiment generation
# ---------------------------------------------------------------------------

_SENTIMENT_TEMPLATES = {
    ("Batsmen", "elite"): {"injury_risk": "Low", "sentiment_score": 80, "news_summary": "Established top-order batter. Consistent performer in T20 franchise leagues."},
    ("Batsmen", "premium"): {"injury_risk": "Low", "sentiment_score": 72, "news_summary": "Proven middle-order talent with franchise T20 experience."},
    ("Batsmen", "standard"): {"injury_risk": "Low", "sentiment_score": 60, "news_summary": "Promising batter looking to cement IPL spot with consistent performances."},
    ("Batsmen", "budget"): {"injury_risk": "Low", "sentiment_score": 50, "news_summary": "Young/uncapped batter with domestic cricket potential."},
    ("Wicketkeepers", "elite"): {"injury_risk": "Low", "sentiment_score": 82, "news_summary": "Premium wicketkeeper-batter. Key franchise player with proven match-winning ability."},
    ("Wicketkeepers", "premium"): {"injury_risk": "Low", "sentiment_score": 68, "news_summary": "Solid keeper-bat option. Reliable behind stumps with handy batting contributions."},
    ("Wicketkeepers", "standard"): {"injury_risk": "Low", "sentiment_score": 55, "news_summary": "Backup wicketkeeper option with developing batting skills."},
    ("Wicketkeepers", "budget"): {"injury_risk": "Low", "sentiment_score": 45, "news_summary": "Young keeper prospect with domestic cricket experience."},
    ("All Rounders", "elite"): {"injury_risk": "Medium", "sentiment_score": 82, "news_summary": "High-impact all-rounder. Capable of game-changing performances with bat and ball."},
    ("All Rounders", "premium"): {"injury_risk": "Low", "sentiment_score": 70, "news_summary": "Useful all-round option. Provides balance to the team with dual skills."},
    ("All Rounders", "standard"): {"injury_risk": "Low", "sentiment_score": 58, "news_summary": "Developing all-rounder with potential in domestic cricket circuit."},
    ("All Rounders", "budget"): {"injury_risk": "Low", "sentiment_score": 48, "news_summary": "Young all-round prospect. Limited franchise experience."},
    ("Fast Bowlers", "elite"): {"injury_risk": "Medium", "sentiment_score": 82, "news_summary": "Premium fast bowler. Key wicket-taking threat across all phases of T20 innings."},
    ("Fast Bowlers", "premium"): {"injury_risk": "Medium", "sentiment_score": 68, "news_summary": "Experienced pacer with ability to bowl in powerplay and death overs."},
    ("Fast Bowlers", "standard"): {"injury_risk": "Low", "sentiment_score": 55, "news_summary": "Developing pace bowler with raw pace or good variations."},
    ("Fast Bowlers", "budget"): {"injury_risk": "Low", "sentiment_score": 42, "news_summary": "Young fast bowler from domestic circuit. Limited T20 franchise exposure."},
    ("Spinners", "elite"): {"injury_risk": "Low", "sentiment_score": 85, "news_summary": "Elite spinner. Match-winning wicket-taker with excellent economy in middle overs."},
    ("Spinners", "premium"): {"injury_risk": "Low", "sentiment_score": 68, "news_summary": "Quality spinner with proven T20 record. Controls middle overs well."},
    ("Spinners", "standard"): {"injury_risk": "Low", "sentiment_score": 55, "news_summary": "Spin bowling option with decent T20 experience."},
    ("Spinners", "budget"): {"injury_risk": "Low", "sentiment_score": 42, "news_summary": "Young spin prospect. Developing skills in domestic cricket."},
}


def generate_news_sentiment(player_id: str, role: str, base_price: int) -> dict:
    """⚠️ SYNTHETIC/FAKE — retired. Returns md5-seeded template "sentiment".

    This is NOT real-time news sentiment (there is no news feed in this
    project). The default pipeline no longer calls it; kept only so the legacy
    ``run_enrichment.py`` demo path still runs. Do not present as real.
    """
    tier = price_tier(base_price)
    seed = _seed_from_id(player_id + "_news")

    template = _SENTIMENT_TEMPLATES.get((role, tier), _SENTIMENT_TEMPLATES[("Batsmen", "standard")])

    # Vary the sentiment score slightly
    sentiment = max(10, min(100, int(template["sentiment_score"] + (seed - 0.5) * 20)))

    # Some variation in injury risk for higher-tier pace bowlers
    injury = template["injury_risk"]
    if role == "Fast Bowlers" and tier in ("elite", "premium") and seed > 0.7:
        injury = "High"

    return {
        "injury_risk": injury,
        "sentiment_score": sentiment,
        "news_summary": template["news_summary"],
    }
