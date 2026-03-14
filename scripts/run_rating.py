#!/usr/bin/env python3
"""
Run Phase 3: Player Rating Engine

Computes ratings from enriched datasets and outputs derived_scores.csv.

Usage:
    python scripts/run_rating.py
"""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.rating.rating_model import RatingEngine


def main():
    print("=" * 65)
    print("  IPL Auction Simulator — Phase 3: Player Rating Engine")
    print("=" * 65)

    # Load and compute
    engine = RatingEngine(config.ENRICHED_DATA_DIR)
    print("\n   📥 Loading enriched datasets...")
    engine.load_data()

    print("\n   🧮 Computing ratings...")
    engine.compute_ratings()

    # Write output
    path = engine.write_csv()
    print(f"\n   💾 Wrote {len(engine.results)} ratings to {path}")

    # Load player names for display
    names = {}
    roles = {}
    with open(config.PLAYERS_MASTER_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            names[row["Player_ID"]] = row["Player Name"]
            roles[row["Player_ID"]] = row["Role"]

    # --- Rating Distribution ---
    print("\n" + "=" * 65)
    print("  📊 Rating Distribution")
    print("=" * 65)

    for label, key in [("Batting", "bat_rating"), ("Bowling", "bowl_rating"),
                        ("Overall", "overall_rating")]:
        values = [r[key] for r in engine.results]
        avg = sum(values) / len(values)
        mn, mx = min(values), max(values)
        # Histogram buckets
        buckets = [0] * 5  # 0-20, 20-40, 40-60, 60-80, 80-100
        for v in values:
            idx = min(4, int(v / 20))
            buckets[idx] += 1
        hist = "  ".join(f"{i*20}-{(i+1)*20}: {buckets[i]}" for i in range(5))
        print(f"\n   {label:10s}  avg={avg:.1f}  min={mn:.1f}  max={mx:.1f}")
        print(f"              {hist}")

    # --- Top 10 Batters ---
    batters = [r for r in engine.results if roles[r["Player_ID"]] in ("Batsmen", "Wicketkeepers")]
    batters.sort(key=lambda x: x["bat_rating"], reverse=True)

    print("\n" + "─" * 65)
    print("  🏏 Top 10 Batters")
    print("─" * 65)
    print(f"   {'Rank':>4}  {'Player':<22} {'Bat':>5} {'PP':>5} {'Mid':>5} "
          f"{'Death':>5} {'vsPace':>6} {'vsSpin':>6} {'Overall':>7}")
    for i, r in enumerate(batters[:10], 1):
        name = names[r["Player_ID"]][:20]
        print(f"   {i:>4}  {name:<22} {r['bat_rating']:>5.1f} "
              f"{r['powerplay_rating']:>5.1f} {r['middle_rating']:>5.1f} "
              f"{r['death_rating']:>5.1f} {r['vs_pace_rating']:>6.1f} "
              f"{r['vs_spin_rating']:>6.1f} {r['overall_rating']:>7.1f}")

    # --- Top 10 Bowlers ---
    bowlers = [r for r in engine.results if roles[r["Player_ID"]] in ("Fast Bowlers", "Spinners")]
    bowlers.sort(key=lambda x: x["bowl_rating"], reverse=True)

    print("\n" + "─" * 65)
    print("  🎯 Top 10 Bowlers")
    print("─" * 65)
    print(f"   {'Rank':>4}  {'Player':<22} {'Bowl':>5} {'PP':>5} {'Mid':>5} "
          f"{'Death':>5} {'Overall':>7}")
    for i, r in enumerate(bowlers[:10], 1):
        name = names[r["Player_ID"]][:20]
        print(f"   {i:>4}  {name:<22} {r['bowl_rating']:>5.1f} "
              f"{r['powerplay_rating']:>5.1f} {r['middle_rating']:>5.1f} "
              f"{r['death_rating']:>5.1f} {r['overall_rating']:>7.1f}")

    # --- Top 10 All-Rounders ---
    ars = [r for r in engine.results if roles[r["Player_ID"]] == "All Rounders"]
    ars.sort(key=lambda x: x["allround_value"], reverse=True)

    print("\n" + "─" * 65)
    print("  ⭐ Top 10 All-Rounders")
    print("─" * 65)
    print(f"   {'Rank':>4}  {'Player':<22} {'Bat':>5} {'Bowl':>5} "
          f"{'AR Val':>6} {'Overall':>7}")
    for i, r in enumerate(ars[:10], 1):
        name = names[r["Player_ID"]][:20]
        print(f"   {i:>4}  {name:<22} {r['bat_rating']:>5.1f} "
              f"{r['bowl_rating']:>5.1f} {r['allround_value']:>6.1f} "
              f"{r['overall_rating']:>7.1f}")

    print("\n" + "=" * 65)
    print("  ✅ Phase 3 complete — Player ratings generated")
    print("=" * 65)


if __name__ == "__main__":
    main()
