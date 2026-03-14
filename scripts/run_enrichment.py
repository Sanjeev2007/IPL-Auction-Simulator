#!/usr/bin/env python3
"""
Run Phase 2: Dataset Enrichment

Generates all 4 enrichment datasets:
  1. ipl_stats_5y.csv
  2. other_t20_stats_5y.csv
  3. recent_form_12m.csv
  4. news_sentiment.csv

Usage:
    python scripts/run_enrichment.py
"""

import sys
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.enrichment.ipl_stats_fetcher import run as run_ipl
from src.enrichment.t20_stats_fetcher import run as run_t20
from src.enrichment.recent_form_fetcher import run as run_recent
from src.enrichment.news_analyzer import run as run_news


def count_master_players() -> int:
    with open(config.PLAYERS_MASTER_PATH, "r", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def show_sample(path: Path, n: int = 3):
    """Print first n rows of a CSV file."""
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for i, row in enumerate(reader):
            if i >= n:
                break
            rows.append(row)

    if rows:
        headers = list(rows[0].keys())
        # Print header
        print(f"\n   {'  |  '.join(h[:18] for h in headers)}")
        print(f"   {'─' * (len(headers) * 20)}")
        for row in rows:
            vals = [str(row[h])[:18] for h in headers]
            print(f"   {'  |  '.join(vals)}")


def main():
    total_master = count_master_players()
    print("=" * 65)
    print("  IPL Auction Simulator — Phase 2: Dataset Enrichment")
    print(f"  Players in master: {total_master}")
    print("=" * 65)

    # Run all 4 enrichment modules
    counts = {}
    counts["ipl"] = run_ipl()
    counts["t20"] = run_t20()
    counts["recent"] = run_recent()
    counts["news"] = run_news()

    # Summary
    print("\n" + "=" * 65)
    print("  📊 Enrichment Summary")
    print("=" * 65)

    files = {
        "ipl_stats_5y.csv": (config.ENRICHED_DATA_DIR / "ipl_stats_5y.csv", counts["ipl"]),
        "other_t20_stats_5y.csv": (config.ENRICHED_DATA_DIR / "other_t20_stats_5y.csv", counts["t20"]),
        "recent_form_12m.csv": (config.ENRICHED_DATA_DIR / "recent_form_12m.csv", counts["recent"]),
        "news_sentiment.csv": (config.ENRICHED_DATA_DIR / "news_sentiment.csv", counts["news"]),
    }

    for name, (path, count) in files.items():
        status = "✅" if count >= total_master else "⚠️"
        print(f"   {status} {name:30s} {count} players")

    # Show sample rows from each file
    print("\n" + "─" * 65)
    print("  📋 Sample Rows")
    print("─" * 65)

    for name, (path, _) in files.items():
        print(f"\n   ── {name} ──")
        show_sample(path, n=3)

    print("\n" + "=" * 65)
    print(f"  ✅ Phase 2 complete — all datasets generated")
    print("=" * 65)


if __name__ == "__main__":
    main()
