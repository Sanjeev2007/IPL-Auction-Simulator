"""
Real Stat Extractor — Computes player statistics from Cricsheet delivery data.

Aggregates ball-by-ball deliveries into batting, bowling, phase, and matchup
stats for each matched player. Filters to the player's last 5 years of activity.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta

from .cricsheet_parser import Delivery, get_phase
from .name_matcher import PlayerNameMatcher


# ---------------------------------------------------------------------------
# Internal accumulators
# ---------------------------------------------------------------------------

class _BatAccum:
    """Accumulates batting stats for a player in a specific context."""
    __slots__ = ("matches", "runs", "balls", "fours", "sixes",
                 "dismissals", "match_ids")

    def __init__(self):
        self.matches = set()
        self.runs = 0
        self.balls = 0
        self.fours = 0
        self.sixes = 0
        self.dismissals = 0
        self.match_ids = set()

    @property
    def strike_rate(self) -> float:
        return round((self.runs / self.balls) * 100, 1) if self.balls else 0.0

    @property
    def average(self) -> float:
        return round(self.runs / self.dismissals, 1) if self.dismissals else self.runs

    @property
    def boundary_pct(self) -> float:
        boundaries = (self.fours * 4 + self.sixes * 6)
        return round(boundaries / self.runs * 100, 1) if self.runs else 0.0

    @property
    def num_matches(self) -> int:
        return len(self.matches)


class _BowlAccum:
    __slots__ = ("matches", "runs_conceded", "balls", "wickets",
                 "wides", "noballs", "match_ids")

    def __init__(self):
        self.matches = set()
        self.runs_conceded = 0
        self.balls = 0  # legal deliveries only
        self.wickets = 0
        self.wides = 0
        self.noballs = 0
        self.match_ids = set()

    @property
    def economy(self) -> float:
        overs = self.balls / 6
        return round(self.runs_conceded / overs, 1) if overs else 0.0

    @property
    def bowling_sr(self) -> float:
        return round(self.balls / self.wickets, 1) if self.wickets else 0.0

    @property
    def num_matches(self) -> int:
        return len(self.matches)


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------

class RealStatExtractor:
    """Compute player stats from raw Delivery data."""

    def __init__(self, matcher: PlayerNameMatcher, years_window: int = 5):
        self.matcher = matcher
        self.years_window = years_window

        # Accumulators keyed by (player_id, league)
        self.bat_stats: dict[tuple[str, str], _BatAccum] = defaultdict(_BatAccum)
        self.bowl_stats: dict[tuple[str, str], _BowlAccum] = defaultdict(_BowlAccum)

        # Phase-specific accumulators keyed by (player_id, league, phase)
        self.bat_phase: dict[tuple[str, str, str], _BatAccum] = defaultdict(_BatAccum)
        self.bowl_phase: dict[tuple[str, str, str], _BowlAccum] = defaultdict(_BowlAccum)

        # Matchup accumulators: (batter_player_id, bowler_type) → _BatAccum
        self.bat_matchup: dict[tuple[str, str], _BatAccum] = defaultdict(_BatAccum)

        # Recent-form accumulators (last 12 months, all leagues combined),
        # keyed by player_id. Real replacement for the old md5-synthetic form.
        self.recent_bat: dict[str, _BatAccum] = defaultdict(_BatAccum)
        self.recent_bowl: dict[str, _BowlAccum] = defaultdict(_BowlAccum)
        self.recent_cutoff: str = ""

        # Bowler type lookup: Player_ID → "pace" | "spin" | None
        self._bowler_type_by_pid: dict[str, str] = {}
        # Cricsheet name → bowler type (for bowlers NOT in our master)
        self._bowler_type_cache: dict[str, str | None] = {}

        # Stats
        self.total_deliveries = 0
        self.matched_deliveries = 0
        self.matchup_deliveries = 0
        self.cutoff_date: str = ""

    def load_bowler_types(self, master_path: Path) -> None:
        """Build bowler-type lookup from players_master.csv."""
        with open(master_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pid = row["Player_ID"]
                role = row["Role"]
                bowling_style = row.get("Bowling Style", "Unknown")

                if role == "Fast Bowlers":
                    self._bowler_type_by_pid[pid] = "pace"
                elif role == "Spinners":
                    self._bowler_type_by_pid[pid] = "spin"
                elif role == "All Rounders":
                    # Classify all-rounders by bowling style
                    bs = bowling_style.lower()
                    if any(k in bs for k in ("spin", "leg", "off", "slow")):
                        self._bowler_type_by_pid[pid] = "spin"
                    else:
                        self._bowler_type_by_pid[pid] = "pace"
                # Batsmen/WK don't get a bowler type

        pace_count = sum(1 for v in self._bowler_type_by_pid.values() if v == "pace")
        spin_count = sum(1 for v in self._bowler_type_by_pid.values() if v == "spin")
        print(f"   🏷️  Bowler types loaded: {pace_count} pace, {spin_count} spin")

    def _get_bowler_type(self, bowler_cricsheet_name: str) -> str | None:
        """Determine if a bowler is pace or spin."""
        # Check cache first
        if bowler_cricsheet_name in self._bowler_type_cache:
            return self._bowler_type_cache[bowler_cricsheet_name]

        # Try matching to our master list
        pid = self.matcher.match(bowler_cricsheet_name)
        if pid and pid in self._bowler_type_by_pid:
            btype = self._bowler_type_by_pid[pid]
            self._bowler_type_cache[bowler_cricsheet_name] = btype
            return btype

        # Heuristic: unknown bowler — can't classify reliably
        self._bowler_type_cache[bowler_cricsheet_name] = None
        return None

    def compute_cutoff(self, deliveries: list[Delivery]) -> str:
        """Find the latest date and set cutoff to 5 years before."""
        dates = [d.date for d in deliveries if d.date != "unknown"]
        if dates:
            latest = max(dates)
            latest_year = int(latest[:4])
            cutoff_year = latest_year - self.years_window
            self.cutoff_date = f"{cutoff_year}-01-01"
            # Recent form = trailing 12 months from the latest match date.
            try:
                latest_dt = datetime.strptime(latest, "%Y-%m-%d")
                self.recent_cutoff = (latest_dt - timedelta(days=365)).strftime("%Y-%m-%d")
            except ValueError:
                self.recent_cutoff = f"{latest_year - 1}-01-01"
        else:
            self.cutoff_date = "2020-01-01"
            self.recent_cutoff = "2023-01-01"
        return self.cutoff_date

    def process(self, deliveries: list[Delivery]) -> None:
        """Process all deliveries and aggregate into player stats."""
        self.compute_cutoff(deliveries)
        print(f"   📅 Date cutoff: matches from {self.cutoff_date} onwards")

        for d in deliveries:
            self.total_deliveries += 1

            # Filter by date
            if d.date < self.cutoff_date:
                continue

            league = d.league

            # --- Batting ---
            batter_pid = self.matcher.match(d.batter)
            if batter_pid and not d.is_wide:
                key = (batter_pid, league)
                acc = self.bat_stats[key]
                acc.matches.add(d.match_id)
                acc.runs += d.batter_runs
                acc.balls += 1
                if d.is_boundary_four:
                    acc.fours += 1
                if d.is_boundary_six:
                    acc.sixes += 1

                # Phase stats
                phase = get_phase(d.over)
                pkey = (batter_pid, league, phase)
                pacc = self.bat_phase[pkey]
                pacc.runs += d.batter_runs
                pacc.balls += 1
                if d.is_boundary_four:
                    pacc.fours += 1
                if d.is_boundary_six:
                    pacc.sixes += 1

                # Matchup stats: track batter performance vs pace/spin
                btype = self._get_bowler_type(d.bowler)
                if btype:
                    mkey = (batter_pid, btype)
                    macc = self.bat_matchup[mkey]
                    macc.runs += d.batter_runs
                    macc.balls += 1
                    if d.is_boundary_four:
                        macc.fours += 1
                    if d.is_boundary_six:
                        macc.sixes += 1
                    self.matchup_deliveries += 1

                # Recent form (trailing 12 months, all leagues combined)
                if d.date >= self.recent_cutoff:
                    racc = self.recent_bat[batter_pid]
                    racc.matches.add(d.match_id)
                    racc.runs += d.batter_runs
                    racc.balls += 1
                    if d.is_boundary_four:
                        racc.fours += 1
                    if d.is_boundary_six:
                        racc.sixes += 1

                self.matched_deliveries += 1

            # Batter dismissal
            if d.is_wicket and d.player_out:
                out_pid = self.matcher.match(d.player_out)
                if out_pid:
                    key = (out_pid, league)
                    self.bat_stats[key].dismissals += 1
                    if d.date >= self.recent_cutoff:
                        self.recent_bat[out_pid].dismissals += 1
                    # Matchup dismissal tracking
                    btype = self._get_bowler_type(d.bowler)
                    if btype and d.wicket_kind not in ("run out", "retired hurt", "obstructing the field"):
                        self.bat_matchup[(out_pid, btype)].dismissals += 1

            # --- Bowling ---
            bowler_pid = self.matcher.match(d.bowler)
            if bowler_pid:
                key = (bowler_pid, league)
                acc = self.bowl_stats[key]
                acc.matches.add(d.match_id)
                acc.runs_conceded += d.total_runs

                if not d.is_wide and not d.is_noball:
                    acc.balls += 1
                if d.is_wide:
                    acc.wides += 1
                if d.is_noball:
                    acc.noballs += 1
                if d.is_wicket and d.wicket_kind not in ("run out", "retired hurt", "obstructing the field"):
                    acc.wickets += 1

                # Phase bowling stats
                phase = get_phase(d.over)
                pkey = (bowler_pid, league, phase)
                pacc = self.bowl_phase[pkey]
                pacc.runs_conceded += d.total_runs
                if not d.is_wide and not d.is_noball:
                    pacc.balls += 1
                if d.is_wicket and d.wicket_kind not in ("run out", "retired hurt"):
                    pacc.wickets += 1

                # Recent form (trailing 12 months, all leagues combined)
                if d.date >= self.recent_cutoff:
                    racc = self.recent_bowl[bowler_pid]
                    racc.matches.add(d.match_id)
                    racc.runs_conceded += d.total_runs
                    if not d.is_wide and not d.is_noball:
                        racc.balls += 1
                    if d.is_wicket and d.wicket_kind not in ("run out", "retired hurt", "obstructing the field"):
                        racc.wickets += 1

        print(f"   📊 Processed {self.total_deliveries} total deliveries")
        print(f"   ✓ {self.matched_deliveries} matched to known players")
        print(f"   🏷️  {self.matchup_deliveries} deliveries with bowler-type matchup data")

    # -------------------------------------------------------------------
    # Output generators
    # -------------------------------------------------------------------

    def get_ipl_stats(self) -> list[dict]:
        """Get IPL stats for all players with data."""
        return self._get_league_stats("IPL")

    def get_other_t20_stats(self) -> list[dict]:
        """Get stats from non-IPL leagues."""
        rows = []
        for league in ("T20I", "BBL", "CPL", "PSL"):
            rows.extend(self._get_league_stats(league, include_phase=False))
        return rows

    def _get_league_stats(self, league: str, include_phase: bool = True) -> list[dict]:
        rows = []
        # Collect all player_ids with data in this league
        pids = set()
        for (pid, lg) in self.bat_stats:
            if lg == league:
                pids.add(pid)
        for (pid, lg) in self.bowl_stats:
            if lg == league:
                pids.add(pid)

        for pid in sorted(pids):
            bat = self.bat_stats.get((pid, league), _BatAccum())
            bowl = self.bowl_stats.get((pid, league), _BowlAccum())

            row = {
                "Player_ID": pid,
                "league": league,
                "matches": max(bat.num_matches, bowl.num_matches),
                "runs": bat.runs,
                "balls_faced": bat.balls,
                "batting_average": bat.average,
                "strike_rate": bat.strike_rate,
                "boundary_pct": bat.boundary_pct,
                "fifties": 0,  # would need per-innings tracking
                "hundreds": 0,
                "wickets": bowl.wickets,
                "economy": bowl.economy,
                "bowling_strike_rate": bowl.bowling_sr,
                "balls_bowled": bowl.balls,
            }

            if include_phase:
                for phase in ("powerplay", "middle", "death"):
                    bp = self.bat_phase.get((pid, league, phase), _BatAccum())
                    bwp = self.bowl_phase.get((pid, league, phase), _BowlAccum())
                    row[f"{phase}_sr"] = bp.strike_rate
                    row[f"{phase}_econ"] = bwp.economy

            rows.append(row)

        return rows

    def get_player_matchups(self) -> list[dict]:
        """Get matchup stats (vs pace / vs spin)."""
        rows = []
        for (pid, btype), acc in sorted(self.bat_matchup.items()):
            rows.append({
                "Player_ID": pid,
                "bowler_type": btype,
                "runs": acc.runs,
                "balls": acc.balls,
                "strike_rate": acc.strike_rate,
                "dismissals": acc.dismissals,
            })
        return rows

    def get_recent_form(self) -> list[dict]:
        """Get trailing-12-month form (all leagues combined) per player.

        Real replacement for the old md5-synthetic recent_form generator.
        """
        rows = []
        pids = set(self.recent_bat) | set(self.recent_bowl)
        for pid in sorted(pids):
            bat = self.recent_bat.get(pid, _BatAccum())
            bowl = self.recent_bowl.get(pid, _BowlAccum())
            rows.append({
                "Player_ID": pid,
                "matches_12m": max(bat.num_matches, bowl.num_matches),
                "runs_12m": bat.runs,
                "avg_12m": bat.average,
                "sr_12m": bat.strike_rate,
                "wickets_12m": bowl.wickets,
                "econ_12m": bowl.economy,
            })
        return rows

    def get_players_with_data(self) -> set[str]:
        """Return set of Player_IDs that have any real data."""
        pids = set()
        for (pid, _) in self.bat_stats:
            pids.add(pid)
        for (pid, _) in self.bowl_stats:
            pids.add(pid)
        return pids
