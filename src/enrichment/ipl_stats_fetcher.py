"""
IPL Stats Fetcher — generates ipl_stats_5y.csv

For each player in players_master.csv, produces aggregated IPL statistics
across their most recent 5 IPL seasons. Uses the knowledge base for known
players and the stat generator for others.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.enrichment.player_knowledge import IPL_KNOWN_STATS
from src.enrichment.stat_generator import generate_ipl_stats

OUTPUT_PATH = config.ENRICHED_DATA_DIR / "ipl_stats_5y.csv"

FIELDNAMES = [
    "Player_ID", "matches", "runs", "batting_average", "strike_rate",
    "fifties", "hundreds", "wickets", "economy", "bowling_strike_rate",
    "powerplay_sr", "middle_sr", "death_sr",
    "powerplay_econ", "middle_econ", "death_econ",
]


def fetch_all() -> list[dict]:
    """Read players_master and generate IPL stats for every player."""
    players = _read_master()
    results = []

    known_count = 0
    generated_count = 0

    for i, p in enumerate(players, 1):
        pid = p["Player_ID"]
        role = p["Role"]
        price = int(p["Base Price (INR)"])

        if pid in IPL_KNOWN_STATS:
            stats = IPL_KNOWN_STATS[pid].copy()
            known_count += 1
            source = "KB"
        else:
            stats = generate_ipl_stats(pid, role, price)
            generated_count += 1
            source = "GEN"

        row = {"Player_ID": pid}
        row.update(stats)
        results.append(row)

        if i % 50 == 0 or i == len(players):
            print(f"   📊 IPL Stats: {i}/{len(players)} processed [{source}]")

    print(f"   → {known_count} from knowledge base, {generated_count} generated")
    return results


def write_csv(rows: list[dict]) -> Path:
    """Write results to CSV."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, 0) for k in FIELDNAMES})
    return OUTPUT_PATH


def _read_master() -> list[dict]:
    with open(config.PLAYERS_MASTER_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run() -> int:
    """Main entry point. Returns number of records written."""
    print("\n🏏 Generating IPL 5-Year Statistics...")
    rows = fetch_all()
    path = write_csv(rows)
    print(f"   ✅ Wrote {len(rows)} records to {path}")
    return len(rows)


if __name__ == "__main__":
    run()
