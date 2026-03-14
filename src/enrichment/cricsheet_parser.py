"""
Cricsheet JSON Parser — Ingests ball-by-ball match data.

Parses Cricsheet JSON files into a flat list of delivery records
that can be aggregated into player statistics.

Each delivery record contains:
  - match metadata (date, teams, league)
  - batter/bowler names
  - runs scored, extras, wickets
  - over number (for phase classification)
"""

from __future__ import annotations

import json
import glob
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Delivery:
    """Single ball/delivery from a match."""
    match_id: str
    date: str             # YYYY-MM-DD
    league: str           # "IPL", "T20I", "BBL", etc.
    batting_team: str
    bowling_team: str
    over: int             # 0-indexed (0-19)
    ball: int             # delivery number within over
    batter: str           # e.g. "V Kohli"
    bowler: str           # e.g. "JJ Bumrah"
    non_striker: str
    batter_runs: int
    extras: int
    total_runs: int
    is_wicket: bool
    wicket_kind: str      # "bowled", "caught", "lbw", etc.
    player_out: str       # who got out
    is_wide: bool
    is_noball: bool
    is_boundary_four: bool
    is_boundary_six: bool


def get_phase(over: int) -> str:
    """Classify over into match phase."""
    if over < 6:
        return "powerplay"
    elif over < 16:
        return "middle"
    else:
        return "death"


def parse_match_file(filepath: str, league: str) -> list[Delivery]:
    """Parse a single Cricsheet JSON file into Delivery records."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    info = data.get("info", {})
    match_id = os.path.basename(filepath).replace(".json", "")
    dates = info.get("dates", [])
    date = str(dates[0]) if dates else "unknown"
    teams = info.get("teams", [])

    deliveries = []

    for innings in data.get("innings", []):
        batting_team = innings.get("team", "")
        bowling_team = [t for t in teams if t != batting_team]
        bowling_team = bowling_team[0] if bowling_team else ""

        for over_data in innings.get("overs", []):
            over_num = over_data.get("over", 0)

            for ball_idx, ball in enumerate(over_data.get("deliveries", [])):
                runs = ball.get("runs", {})
                extras = ball.get("extras", {})
                wickets = ball.get("wickets", [])

                batter_runs = runs.get("batter", 0)
                is_wide = "wides" in extras
                is_noball = "noballs" in extras

                # Wicket info
                is_wicket = len(wickets) > 0
                wicket_kind = ""
                player_out = ""
                if is_wicket:
                    w = wickets[0]
                    wicket_kind = w.get("kind", "")
                    player_out = w.get("player_out", "")

                deliveries.append(Delivery(
                    match_id=match_id,
                    date=date,
                    league=league,
                    batting_team=batting_team,
                    bowling_team=bowling_team,
                    over=over_num,
                    ball=ball_idx,
                    batter=ball.get("batter", ""),
                    bowler=ball.get("bowler", ""),
                    non_striker=ball.get("non_striker", ""),
                    batter_runs=batter_runs,
                    extras=runs.get("extras", 0),
                    total_runs=runs.get("total", 0),
                    is_wicket=is_wicket,
                    wicket_kind=wicket_kind,
                    player_out=player_out,
                    is_wide=is_wide,
                    is_noball=is_noball,
                    is_boundary_four=(batter_runs == 4),
                    is_boundary_six=(batter_runs == 6),
                ))

    return deliveries


def parse_league_directory(directory: str, league: str) -> list[Delivery]:
    """Parse all JSON files in a league directory."""
    pattern = os.path.join(directory, "*.json")
    files = sorted(glob.glob(pattern))
    all_deliveries = []

    for i, f in enumerate(files):
        try:
            all_deliveries.extend(parse_match_file(f, league))
        except (json.JSONDecodeError, KeyError) as e:
            pass  # Skip corrupt files silently

        if (i + 1) % 200 == 0:
            print(f"      Parsed {i+1}/{len(files)} {league} matches...")

    print(f"      ✓ {league}: {len(files)} matches, {len(all_deliveries)} deliveries")
    return all_deliveries


def load_all_data(cricsheet_dir: str) -> list[Delivery]:
    """Load all Cricsheet data from the given directory."""
    leagues = {
        "ipl": "IPL",
        "t20i": "T20I",
        "bbl": "BBL",
        "cpl": "CPL",
        "psl": "PSL",
    }

    all_deliveries = []
    for folder, league_name in leagues.items():
        league_dir = os.path.join(cricsheet_dir, folder)
        if os.path.exists(league_dir):
            print(f"   📂 Loading {league_name}...")
            all_deliveries.extend(parse_league_directory(league_dir, league_name))
        else:
            print(f"   ⚠ {league_name} directory not found: {league_dir}")

    print(f"\n   📊 Total: {len(all_deliveries)} deliveries loaded")
    return all_deliveries
