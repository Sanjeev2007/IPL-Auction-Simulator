#!/usr/bin/env python3
"""
Run Phase 5: Full Tournament Simulation

Simulates 1 verbose season, then 500 seasons for aggregate analytics.
Saves results to output/tournament_results.csv.
"""

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.player import Player, Role
from src.models.team import Team
from src.simulation.league_engine import simulate_season, simulate_multiple_seasons


def load_players() -> dict[str, Player]:
    players = {}
    with open(config.PLAYERS_MASTER_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = row["Player_ID"]
            players[pid] = Player(
                player_id=pid,
                name=row["Player Name"],
                role=Role.from_csv(row["Role"]),
                base_price=int(row["Base Price (INR)"])
            )
    with open(config.DERIVED_SCORES_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = row["Player_ID"]
            if pid in players:
                players[pid].bat_rating = float(row["bat_rating"])
                players[pid].bowl_rating = float(row["bowl_rating"])
                players[pid].allround_value = float(row["allround_value"])
                players[pid].overall_rating = float(row["overall_rating"])
    return players


def build_teams(
    players: dict[str, Player],
    roster_data: dict[str, dict],
) -> list[Team]:
    """Build ``Team`` objects from an arbitrary roster spec.

    This is the team-count-agnostic core used by both the JSON loader and any
    caller supplying teams dynamically (e.g. the API / future auction). It
    accepts *any* number of teams — the simulation engine and playoff bracket
    scale to whatever is passed in.

    ``roster_data`` maps ``team_id`` → ``{"batting_order": [pid, ...] (11),
    "bowlers": [pid, ...], "name": <optional display name>}``. All player IDs
    must resolve against ``players`` (loaded from ``players_master.csv``).
    """
    teams: list[Team] = []
    for team_id, tdata in roster_data.items():
        batting_pids = tdata["batting_order"]
        bowler_pids = tdata["bowlers"]
        if len(batting_pids) != 11:
            raise ValueError(f"Team {team_id}: batting_order must have exactly 11 players")
        t = Team(team_id=team_id, name=tdata.get("name", team_id))
        for pid in batting_pids:
            if pid not in players:
                raise ValueError(f"Player {pid} in {team_id} not found in players_master.csv")
            t.playing_xi.append(players[pid])
            t.batting_order.append(players[pid])
        for pid in bowler_pids:
            if pid not in players:
                raise ValueError(f"Bowler {pid} in {team_id} not found in players_master.csv")
            t.bowling_plan.append((players[pid], 4))
        teams.append(t)
    return teams


def load_teams(
    players: dict[str, Player],
    teams_path: str | Path | None = None,
) -> list[Team]:
    """Load teams from a lineup JSON file (defaults to the bundled 6 teams).

    Pass ``teams_path`` to load a different lineup file, or call
    :func:`build_teams` directly to supply rosters without touching disk.
    """
    teams_path = Path(teams_path) if teams_path else Path(config.DATA_DIR) / "teams" / "team_lineups.json"
    if not teams_path.exists():
        raise FileNotFoundError(f"Missing {teams_path}. Provide team_lineups.json manually.")
    with open(teams_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return build_teams(players, data)


def main():
    print("=" * 65)
    print("  IPL Auction Simulator — Phase 5: Tournament Engine")
    print("=" * 65)

    players = load_players()
    teams = load_teams(players)
    print(f"\n   📋 {len(players)} players loaded")
    print(f"   🏟️  {len(teams)} teams loaded")

    # ── 1 Verbose Season ──
    print("\n" + "─" * 65)
    print("  🏏 Simulating 1 Full Season (verbose)")
    print("─" * 65 + "\n")

    result = simulate_season(teams, verbose=True)

    # ── 500 Seasons ──
    print("\n" + "─" * 65)
    print("  📊 Simulating 500 Seasons...")
    print("─" * 65 + "\n")

    agg = simulate_multiple_seasons(teams, n=500)

    # Sort by championship probability
    ranked = sorted(agg.items(), key=lambda x: x[1]["championship_probability"], reverse=True)

    print(f"\n   {'Team':<6} {'Champ%':>7} {'Final%':>7} {'PO%':>6} {'AvgPts':>7}")
    print(f"   {'─' * 40}")
    for tid, d in ranked:
        print(f"   {tid:<6} {d['championship_probability']:>6.1f}% "
              f"{d['finals_probability']:>6.1f}% "
              f"{d['playoff_probability']:>5.1f}% "
              f"{d['average_points']:>7.1f}")

    # ── Save to CSV ──
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / "tournament_results.csv"

    fieldnames = [
        "team_id", "team_name", "championship_probability", "finals_probability",
        "playoff_probability", "average_points", "championships", "finals",
        "playoffs", "total_points", "seasons",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tid, d in ranked:
            writer.writerow({"team_id": tid, **d})

    print(f"\n   💾 Results saved to {out_path}")

    print("\n" + "=" * 65)
    print("  ✅ Phase 5 complete — Tournament Simulation Engine verified")
    print("=" * 65)


if __name__ == "__main__":
    main()
