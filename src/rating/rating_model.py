"""
Player Rating Model — Phase 3

Computes player ratings (0–100 scale) from enriched datasets.

Rating Components:
  bat_rating       = 0.60×IPL + 0.25×T20 + 0.15×recent_form
  bowl_rating      = 0.60×IPL + 0.25×T20 + 0.15×recent_form
  allround_value   = weighted(bat_rating, bowl_rating) based on role
  overall_rating   = 0.85×performance + 0.10×popularity + 0.05×news

Phase ratings:
  powerplay_rating, middle_rating, death_rating

Matchup ratings:
  vs_pace_rating, vs_spin_rating
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def _percentile_rank(value: float, all_values: list[float]) -> float:
    """Compute percentile rank (0–100) of a value within a distribution."""
    if not all_values:
        return 50.0
    below = sum(1 for v in all_values if v < value)
    equal = sum(1 for v in all_values if v == value)
    rank = (below + 0.5 * equal) / len(all_values) * 100
    return _clamp(rank)


# ---------------------------------------------------------------------------
# Sub-rating calculators
# ---------------------------------------------------------------------------

def _bat_sub_rating(runs: float, avg: float, sr: float,
                    matches: int, boundary_pct: float) -> float:
    """
    Compute batting sub-rating from raw stats.

    Factors:
      - Average (consistency) — 35%
      - Strike rate (aggression) — 30%
      - Volume (runs × matches) — 20%
      - Boundary % (impact) — 15%
    """
    # Normalize each factor to approx 0-100
    avg_score = _clamp(avg / 50.0 * 100)        # avg 50 → 100
    sr_score = _clamp((sr - 80) / 100 * 100)     # SR 180 → 100, SR 80 → 0
    vol_score = _clamp(runs / 2500 * 100)         # 2500 runs → 100
    bnd_score = _clamp(boundary_pct / 80 * 100)   # 80% boundary → 100

    return (0.35 * avg_score + 0.30 * sr_score +
            0.20 * vol_score + 0.15 * bnd_score)


def _bowl_sub_rating(wickets: float, economy: float, bowl_sr: float,
                     matches: int, balls: int) -> float:
    """
    Compute bowling sub-rating from raw stats.

    Factors:
      - Economy (containment) — 30%
      - Bowling SR (wicket-taking) — 30%
      - Wickets volume — 25%
      - Matches experience — 15%
    """
    if balls < 6:  # less than 1 over bowled
        return 0.0

    # Economy: lower is better (6.0 → 100, 12.0 → 0)
    econ_score = _clamp((12.0 - economy) / 6.0 * 100)
    # Bowling SR: lower is better (12 → 100, 36 → 0)
    sr_score = _clamp((36.0 - bowl_sr) / 24.0 * 100) if bowl_sr > 0 else 0
    # Wickets volume
    wkt_score = _clamp(wickets / 80 * 100)
    # Experience
    exp_score = _clamp(matches / 60 * 100)

    return (0.30 * econ_score + 0.30 * sr_score +
            0.25 * wkt_score + 0.15 * exp_score)


def _phase_bat_rating(sr: float) -> float:
    """Convert phase strike rate to 0-100 rating."""
    if sr <= 0:
        return 0.0
    return _clamp((sr - 80) / 120 * 100)  # SR 200 → 100, SR 80 → 0


def _phase_bowl_rating(econ: float) -> float:
    """Convert phase economy to 0-100 rating (lower econ = higher rating)."""
    if econ <= 0:
        return 0.0
    return _clamp((14.0 - econ) / 8.0 * 100)  # econ 6 → 100, econ 14 → 0


def _matchup_rating(sr: float, balls: int) -> float:
    """Convert matchup SR to a rating, dampened by sample size."""
    if balls < 10:
        return 50.0  # default for insufficient data
    base = _clamp((sr - 80) / 120 * 100)
    # Dampen toward 50 if sample is small
    confidence = min(1.0, balls / 200)
    return 50.0 + (base - 50.0) * confidence


# ---------------------------------------------------------------------------
# Main Rating Engine
# ---------------------------------------------------------------------------

class RatingEngine:
    """Compute all player ratings from enriched CSVs."""

    def __init__(self, enriched_dir: Path):
        self.enriched_dir = enriched_dir
        self.players: list[dict] = []        # from players_master
        self.ipl_stats: dict[str, dict] = {} # Player_ID → row
        self.t20_stats: dict[str, list] = defaultdict(list)  # Player_ID → [rows]
        self.matchups: dict[str, dict] = defaultdict(dict)   # Player_ID → {pace: row, spin: row}
        self.recent_form: dict[str, dict] = {} # Player_ID → row
        self.news: dict[str, dict] = {}        # Player_ID → row
        self.results: list[dict] = []          # final rated rows

    def load_data(self) -> None:
        """Load all input CSVs."""
        # Players master
        with open(self.enriched_dir / "players_master.csv", "r", encoding="utf-8") as f:
            self.players = list(csv.DictReader(f))
        print(f"   📋 Loaded {len(self.players)} players")

        # IPL stats
        with open(self.enriched_dir / "ipl_stats_5y.csv", "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.ipl_stats[row["Player_ID"]] = row
        print(f"   🏏 Loaded {len(self.ipl_stats)} IPL stat entries")

        # Other T20 stats (aggregate per player across leagues)
        with open(self.enriched_dir / "other_t20_stats_5y.csv", "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.t20_stats[row["Player_ID"]].append(row)
        print(f"   🌍 Loaded T20 stats for {len(self.t20_stats)} players")

        # Player matchups
        matchup_path = self.enriched_dir / "player_matchups.csv"
        if matchup_path.exists():
            with open(matchup_path, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self.matchups[row["Player_ID"]][row["bowler_type"]] = row
        print(f"   🎯 Loaded matchups for {len(self.matchups)} players")

        # Recent form
        with open(self.enriched_dir / "recent_form_12m.csv", "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.recent_form[row["Player_ID"]] = row
        print(f"   📈 Loaded recent form for {len(self.recent_form)} players")

        # News/sentiment
        with open(self.enriched_dir / "news_sentiment.csv", "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.news[row["Player_ID"]] = row
        print(f"   📰 Loaded news for {len(self.news)} players")

    def compute_ratings(self) -> list[dict]:
        """Compute ratings for all players."""
        self.results = []

        for p in self.players:
            pid = p["Player_ID"]
            role = p["Role"]
            result = self._rate_player(pid, role)
            self.results.append(result)

        # Percentile-normalize overall_rating
        all_overall = [r["overall_rating"] for r in self.results]
        for r in self.results:
            r["overall_rating"] = round(
                _percentile_rank(r["overall_rating"], all_overall), 1
            )

        print(f"\n   ✅ Computed ratings for {len(self.results)} players")
        return self.results

    def _rate_player(self, pid: str, role: str) -> dict:
        """Compute all ratings for a single player."""
        ipl = self.ipl_stats.get(pid, {})
        t20_rows = self.t20_stats.get(pid, [])
        matchup = self.matchups.get(pid, {})
        form = self.recent_form.get(pid, {})
        news = self.news.get(pid, {})

        # --- IPL batting sub-rating ---
        ipl_bat = _bat_sub_rating(
            runs=float(ipl.get("runs", 0)),
            avg=float(ipl.get("batting_average", 0)),
            sr=float(ipl.get("strike_rate", 0)),
            matches=int(ipl.get("matches", 0)),
            boundary_pct=float(ipl.get("boundary_pct", 0)),
        )

        # --- IPL bowling sub-rating ---
        ipl_bowl = _bowl_sub_rating(
            wickets=float(ipl.get("wickets", 0)),
            economy=float(ipl.get("economy", 0)),
            bowl_sr=float(ipl.get("bowling_strike_rate", 0)),
            matches=int(ipl.get("matches", 0)),
            balls=int(ipl.get("balls_bowled", 0)),
        )

        # --- Aggregate T20 batting/bowling ---
        t20_bat = 0.0
        t20_bowl = 0.0
        if t20_rows:
            t20_runs = sum(float(r.get("runs", 0)) for r in t20_rows)
            t20_matches = sum(int(r.get("matches", 0)) for r in t20_rows)
            # Weighted average SR and avg
            t20_sr = float(t20_rows[0].get("strike_rate", 0)) if t20_rows else 0
            t20_avg = float(t20_rows[0].get("batting_average", 0)) if t20_rows else 0
            t20_wkts = sum(float(r.get("wickets", 0)) for r in t20_rows)
            t20_econ = float(t20_rows[0].get("economy", 0)) if t20_rows else 0

            t20_bat = _bat_sub_rating(t20_runs, t20_avg, t20_sr, t20_matches, 0)
            if t20_wkts > 0 and t20_econ > 0:
                t20_bowl = _bowl_sub_rating(
                    t20_wkts, t20_econ,
                    t20_matches * 24 / t20_wkts if t20_wkts else 0,
                    t20_matches, t20_matches * 24
                )

        # --- Recent form sub-ratings ---
        form_bat = 0.0
        form_bowl = 0.0
        if form:
            form_bat = _bat_sub_rating(
                runs=float(form.get("runs_12m", 0)),
                avg=float(form.get("avg_12m", 0)),
                sr=float(form.get("sr_12m", 0)),
                matches=int(form.get("matches_12m", 0)),
                boundary_pct=0,
            )
            form_econ = float(form.get("econ_12m", 0))
            form_wkts = float(form.get("wickets_12m", 0))
            if form_wkts > 0 and form_econ > 0:
                form_bowl = _bowl_sub_rating(
                    form_wkts, form_econ, 0, int(form.get("matches_12m", 0)), 60
                )

        # --- Weighted batting rating ---
        bat_rating = _clamp(0.60 * ipl_bat + 0.25 * t20_bat + 0.15 * form_bat)

        # --- Weighted bowling rating ---
        bowl_rating = _clamp(0.60 * ipl_bowl + 0.25 * t20_bowl + 0.15 * form_bowl)

        # --- Phase ratings ---
        pp_bat = _phase_bat_rating(float(ipl.get("powerplay_sr", 0)))
        mid_bat = _phase_bat_rating(float(ipl.get("middle_sr", 0)))
        death_bat = _phase_bat_rating(float(ipl.get("death_sr", 0)))

        pp_bowl = _phase_bowl_rating(float(ipl.get("powerplay_econ", 0)))
        mid_bowl = _phase_bowl_rating(float(ipl.get("middle_econ", 0)))
        death_bowl = _phase_bowl_rating(float(ipl.get("death_econ", 0)))

        # Combined phase ratings (bat + bowl weighted by role)
        if role in ("Batsmen", "Wicketkeepers"):
            pp_rating = pp_bat
            mid_rating = mid_bat
            death_rating = death_bat
        elif role in ("Fast Bowlers", "Spinners"):
            pp_rating = pp_bowl
            mid_rating = mid_bowl
            death_rating = death_bowl
        else:  # All Rounders
            pp_rating = 0.5 * pp_bat + 0.5 * pp_bowl
            mid_rating = 0.5 * mid_bat + 0.5 * mid_bowl
            death_rating = 0.5 * death_bat + 0.5 * death_bowl

        # --- Matchup ratings ---
        pace_data = matchup.get("pace", {})
        spin_data = matchup.get("spin", {})
        vs_pace_rating = _matchup_rating(
            float(pace_data.get("strike_rate", 0)),
            int(pace_data.get("balls", 0))
        )
        vs_spin_rating = _matchup_rating(
            float(spin_data.get("strike_rate", 0)),
            int(spin_data.get("balls", 0))
        )

        # --- All-round value ---
        if role == "All Rounders":
            allround_value = 0.45 * bat_rating + 0.45 * bowl_rating + 0.10 * max(bat_rating, bowl_rating)
        elif role in ("Batsmen", "Wicketkeepers"):
            allround_value = 0.85 * bat_rating + 0.15 * bowl_rating
        else:  # bowlers
            allround_value = 0.15 * bat_rating + 0.85 * bowl_rating

        # --- Overall rating ---
        perf_score = allround_value
        popularity = float(news.get("sentiment_score", 50))
        news_context = popularity  # reuse sentiment as context signal

        overall_rating = (0.85 * perf_score +
                          0.10 * popularity +
                          0.05 * news_context)

        return {
            "Player_ID": pid,
            "bat_rating": round(bat_rating, 1),
            "bowl_rating": round(bowl_rating, 1),
            "allround_value": round(allround_value, 1),
            "overall_rating": round(overall_rating, 1),  # will be percentile-normalized later
            "powerplay_rating": round(pp_rating, 1),
            "middle_rating": round(mid_rating, 1),
            "death_rating": round(death_rating, 1),
            "vs_pace_rating": round(vs_pace_rating, 1),
            "vs_spin_rating": round(vs_spin_rating, 1),
        }

    def write_csv(self) -> Path:
        """Write derived_scores.csv."""
        fieldnames = [
            "Player_ID", "bat_rating", "bowl_rating", "allround_value",
            "overall_rating", "powerplay_rating", "middle_rating",
            "death_rating", "vs_pace_rating", "vs_spin_rating",
        ]
        path = self.enriched_dir / "derived_scores.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.results:
                writer.writerow(row)
        return path
