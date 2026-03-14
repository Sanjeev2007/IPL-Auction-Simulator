"""
News Analyzer — generates news_sentiment.csv

For each player, generates contextual signals: injury risk, sentiment score,
and a news summary. Uses the knowledge base for prominent players and
generates template-based entries for others.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.enrichment.player_knowledge import NEWS_KNOWN
from src.enrichment.stat_generator import generate_news_sentiment

OUTPUT_PATH = config.ENRICHED_DATA_DIR / "news_sentiment.csv"

FIELDNAMES = [
    "Player_ID", "injury_risk", "sentiment_score", "news_summary",
]


def fetch_all() -> list[dict]:
    """Generate news/sentiment data for every player."""
    players = _read_master()
    results = []

    known_count = 0
    generated_count = 0

    for i, p in enumerate(players, 1):
        pid = p["Player_ID"]
        role = p["Role"]
        price = int(p["Base Price (INR)"])

        if pid in NEWS_KNOWN:
            data = NEWS_KNOWN[pid].copy()
            known_count += 1
        else:
            data = generate_news_sentiment(pid, role, price)
            generated_count += 1

        row = {"Player_ID": pid}
        row.update(data)
        results.append(row)

        if i % 50 == 0 or i == len(players):
            print(f"   📰 News/Sentiment: {i}/{len(players)} processed")

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
    """Main entry point."""
    print("\n📰 Generating News & Sentiment Analysis...")
    rows = fetch_all()
    path = write_csv(rows)
    print(f"   ✅ Wrote {len(rows)} records to {path}")
    return len(rows)


if __name__ == "__main__":
    run()
