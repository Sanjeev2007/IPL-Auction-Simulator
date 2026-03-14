"""
T20 Stats Fetcher — generates other_t20_stats_5y.csv

For each player, generates statistics from other T20 leagues across their
most recent 5 active years. Players may have multiple rows (one per league).

To ensure exactly N_PLAYERS rows (one per Player_ID) for the primary output,
we also produce a single aggregated row per player.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.enrichment.player_knowledge import T20_KNOWN_STATS
from src.enrichment.stat_generator import generate_t20_stats

OUTPUT_PATH = config.ENRICHED_DATA_DIR / "other_t20_stats_5y.csv"

FIELDNAMES = [
    "Player_ID", "league", "matches", "runs",
    "batting_average", "strike_rate", "wickets", "economy",
]


def fetch_all() -> list[dict]:
    """Generate T20 league stats for every player."""
    players = _read_master()
    results = []

    known_count = 0
    generated_count = 0

    for i, p in enumerate(players, 1):
        pid = p["Player_ID"]
        role = p["Role"]
        price = int(p["Base Price (INR)"])

        if pid in T20_KNOWN_STATS:
            league_entries = T20_KNOWN_STATS[pid]
            known_count += 1
        else:
            league_entries = generate_t20_stats(pid, role, price)
            generated_count += 1

        for entry in league_entries:
            row = {"Player_ID": pid}
            row.update(entry)
            results.append(row)

        if i % 50 == 0 or i == len(players):
            print(f"   🌍 T20 Stats: {i}/{len(players)} players processed")

    print(f"   → {known_count} from knowledge base, {generated_count} generated")
    print(f"   → {len(results)} total league entries (multi-row per player)")
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
    print("\n🌍 Generating Other T20 League Statistics (5-Year)...")
    rows = fetch_all()
    path = write_csv(rows)
    print(f"   ✅ Wrote {len(rows)} league entries to {path}")

    # Count unique players
    unique = len(set(r["Player_ID"] for r in rows))
    print(f"   → Covers {unique} unique players")
    return unique


if __name__ == "__main__":
    run()
