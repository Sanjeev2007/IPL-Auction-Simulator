"""
Recent Form Fetcher — generates recent_form_12m.csv

For each player, generates performance stats from the last 12 months
across all T20 formats.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.enrichment.stat_generator import generate_recent_form

OUTPUT_PATH = config.ENRICHED_DATA_DIR / "recent_form_12m.csv"

FIELDNAMES = [
    "Player_ID", "matches_12m", "runs_12m", "avg_12m",
    "sr_12m", "wickets_12m", "econ_12m",
]


def fetch_all() -> list[dict]:
    """Generate recent form stats for every player."""
    players = _read_master()
    results = []

    for i, p in enumerate(players, 1):
        pid = p["Player_ID"]
        role = p["Role"]
        price = int(p["Base Price (INR)"])

        stats = generate_recent_form(pid, role, price)
        row = {"Player_ID": pid}
        row.update(stats)
        results.append(row)

        if i % 50 == 0 or i == len(players):
            print(f"   📈 Recent Form: {i}/{len(players)} processed")

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
    """Main entry point."""
    print("\n📈 Generating Recent Form (Last 12 Months)...")
    rows = fetch_all()
    path = write_csv(rows)
    print(f"   ✅ Wrote {len(rows)} records to {path}")
    return len(rows)


if __name__ == "__main__":
    run()
