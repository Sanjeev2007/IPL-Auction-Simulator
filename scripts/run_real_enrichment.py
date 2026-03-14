#!/usr/bin/env python3
"""
Run Phase 2 Redesign: Real Cricket Data Pipeline

Ingests Cricsheet ball-by-ball data, matches players to players_master,
computes real statistics, and outputs enriched CSVs.

Usage:
    python scripts/run_real_enrichment.py
"""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.enrichment.cricsheet_parser import load_all_data
from src.enrichment.name_matcher import PlayerNameMatcher
from src.enrichment.stat_extractor import RealStatExtractor
from src.enrichment.stat_generator import (
    generate_ipl_stats, generate_t20_stats, generate_recent_form,
)

CRICSHEET_DIR = config.DATA_DIR / "cricsheet"


def load_master_ids() -> list[dict]:
    """Load all players from players_master.csv."""
    with open(config.PLAYERS_MASTER_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_ipl_stats(extractor: RealStatExtractor, all_players: list[dict]) -> int:
    """Write ipl_stats_5y.csv with real data + fallback."""
    fieldnames = [
        "Player_ID", "data_source", "matches", "runs", "balls_faced",
        "batting_average", "strike_rate", "boundary_pct",
        "fifties", "hundreds", "wickets", "economy",
        "bowling_strike_rate", "balls_bowled",
        "powerplay_sr", "middle_sr", "death_sr",
        "powerplay_econ", "middle_econ", "death_econ",
    ]

    real_stats = {r["Player_ID"]: r for r in extractor.get_ipl_stats()}
    real_count = 0
    fallback_count = 0

    path = config.ENRICHED_DATA_DIR / "ipl_stats_5y.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for p in all_players:
            pid = p["Player_ID"]

            if pid in real_stats and real_stats[pid].get("matches", 0) >= 3:
                row = real_stats[pid]
                row["data_source"] = "real"
                real_count += 1
            else:
                # Fallback to generated stats
                gen = generate_ipl_stats(pid, p["Role"], int(p["Base Price (INR)"]))
                row = {
                    "Player_ID": pid, "data_source": "estimated",
                    "matches": gen["matches"], "runs": gen["runs"],
                    "balls_faced": 0,
                    "batting_average": gen["batting_average"],
                    "strike_rate": gen["strike_rate"],
                    "boundary_pct": 0,
                    "fifties": gen["fifties"], "hundreds": gen["hundreds"],
                    "wickets": gen["wickets"], "economy": gen["economy"],
                    "bowling_strike_rate": gen["bowling_strike_rate"],
                    "balls_bowled": 0,
                    "powerplay_sr": gen["powerplay_sr"],
                    "middle_sr": gen["middle_sr"],
                    "death_sr": gen["death_sr"],
                    "powerplay_econ": gen["powerplay_econ"],
                    "middle_econ": gen["middle_econ"],
                    "death_econ": gen["death_econ"],
                }
                fallback_count += 1

            writer.writerow({k: row.get(k, 0) for k in fieldnames})

    print(f"   ✅ ipl_stats_5y.csv: {real_count} real, {fallback_count} estimated")
    return real_count


def write_other_t20_stats(extractor: RealStatExtractor, all_players: list[dict]) -> int:
    """Write other_t20_stats_5y.csv."""
    fieldnames = [
        "Player_ID", "data_source", "league", "matches", "runs",
        "batting_average", "strike_rate", "wickets", "economy",
    ]

    real_rows = extractor.get_other_t20_stats()
    real_pids = {r["Player_ID"] for r in real_rows}

    path = config.ENRICHED_DATA_DIR / "other_t20_stats_5y.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Write real rows
        for row in real_rows:
            row["data_source"] = "real"
            writer.writerow({k: row.get(k, 0) for k in fieldnames})

        # Fallback for players without real data
        fallback_count = 0
        for p in all_players:
            pid = p["Player_ID"]
            if pid not in real_pids:
                gen_entries = generate_t20_stats(pid, p["Role"], int(p["Base Price (INR)"]))
                for entry in gen_entries:
                    entry["Player_ID"] = pid
                    entry["data_source"] = "estimated"
                    writer.writerow({k: entry.get(k, 0) for k in fieldnames})
                fallback_count += 1

    total_real = len(real_pids)
    print(f"   ✅ other_t20_stats_5y.csv: {total_real} real, {fallback_count} estimated")
    return total_real


def write_player_matchups(extractor: RealStatExtractor) -> int:
    """Write player_matchups.csv."""
    fieldnames = [
        "Player_ID", "bowler_type", "runs", "balls",
        "strike_rate", "dismissals",
    ]

    rows = extractor.get_player_matchups()
    path = config.ENRICHED_DATA_DIR / "player_matchups.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"   ✅ player_matchups.csv: {len(rows)} matchup entries")
    return len(rows)


def show_sample(path: Path, n: int = 3):
    """Print first n rows of a CSV."""
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [next(reader) for _ in range(n)]
    if rows:
        headers = list(rows[0].keys())
        print(f"\n   {'  |  '.join(h[:16] for h in headers)}")
        print(f"   {'─' * min(160, len(headers) * 18)}")
        for row in rows:
            print(f"   {'  |  '.join(str(row[h])[:16] for h in headers)}")


def main():
    print("=" * 65)
    print("  IPL Auction Simulator — Phase 2 Redesign: Real Data Pipeline")
    print("=" * 65)

    # 1. Load players
    all_players = load_master_ids()
    print(f"\n   📋 {len(all_players)} players in master")

    # 2. Build name matcher
    print("\n   🔗 Building name matcher...")
    matcher = PlayerNameMatcher()
    matcher.load_master(config.PLAYERS_MASTER_PATH)

    # 3. Load Cricsheet data
    print("\n   📥 Loading Cricsheet ball-by-ball data...")
    deliveries = load_all_data(str(CRICSHEET_DIR))

    # 4. Extract stats
    print("\n   🧮 Computing player statistics...")
    extractor = RealStatExtractor(matcher, years_window=5)
    extractor.load_bowler_types(config.PLAYERS_MASTER_PATH)
    extractor.process(deliveries)

    # 5. Name matching stats
    match_stats = matcher.get_match_stats()
    print(f"\n   📇 Name matching results:")
    print(f"      Unique Cricsheet names seen: {match_stats['total_unique_names']}")
    print(f"      Matched to our players:      {match_stats['matched']}")
    print(f"      Unmatched:                   {match_stats['unmatched']}")
    print(f"      Match rate:                  {match_stats['match_rate']}%")

    # 6. Players with real data
    real_pids = extractor.get_players_with_data()
    print(f"\n   🏏 Players with real data: {len(real_pids)} / {len(all_players)}")

    # 7. Write output CSVs
    print("\n   📝 Writing output files...")
    ipl_real = write_ipl_stats(extractor, all_players)
    t20_real = write_other_t20_stats(extractor, all_players)
    matchup_count = write_player_matchups(extractor)

    # 8. Summary
    print("\n" + "=" * 65)
    print("  📊 Pipeline Summary")
    print("=" * 65)
    print(f"   Matches processed:      {len(set(d.match_id for d in deliveries if d.date >= extractor.cutoff_date))}")
    print(f"   Deliveries processed:   {extractor.total_deliveries}")
    print(f"   Players with real data: {len(real_pids)} / {len(all_players)} "
          f"({len(real_pids)/len(all_players)*100:.0f}%)")
    print(f"   IPL stats (real):       {ipl_real}")
    print(f"   T20 stats (real):       {t20_real}")
    print(f"   Matchup entries:        {matchup_count}")

    # 9. Sample output
    print("\n" + "─" * 65)
    print("  📋 Sample Rows")
    print("─" * 65)

    for name in ("ipl_stats_5y.csv", "other_t20_stats_5y.csv"):
        p = config.ENRICHED_DATA_DIR / name
        if p.exists():
            print(f"\n   ── {name} ──")
            show_sample(p)

    # 10. Matchup analysis
    matchup_path = config.ENRICHED_DATA_DIR / "player_matchups.csv"
    if matchup_path.exists():
        print(f"\n   ── player_matchups.csv (10 players) ──")
        with open(matchup_path, "r", encoding="utf-8") as f:
            matchup_rows = list(csv.DictReader(f))

        # Show 10 sample players (5 pairs of pace/spin)
        shown_pids = set()
        sample_rows = []
        for r in matchup_rows:
            if r["Player_ID"] not in shown_pids and len(shown_pids) < 10:
                shown_pids.add(r["Player_ID"])
            if r["Player_ID"] in shown_pids:
                sample_rows.append(r)

        if sample_rows:
            headers = list(sample_rows[0].keys())
            print(f"\n   {'  |  '.join(h[:16] for h in headers)}")
            print(f"   {'─' * min(120, len(headers) * 18)}")
            for row in sample_rows:
                print(f"   {'  |  '.join(str(row[h])[:16] for h in headers)}")

        # SR distribution: vs pace vs vs spin
        pace_srs = [float(r["strike_rate"]) for r in matchup_rows if r["bowler_type"] == "pace" and float(r["balls"]) >= 30]
        spin_srs = [float(r["strike_rate"]) for r in matchup_rows if r["bowler_type"] == "spin" and float(r["balls"]) >= 30]

        if pace_srs and spin_srs:
            print(f"\n   📊 Strike Rate Distribution (players with 30+ balls):")
            print(f"      vs Pace  → avg: {sum(pace_srs)/len(pace_srs):.1f}, "
                  f"min: {min(pace_srs):.1f}, max: {max(pace_srs):.1f}, n={len(pace_srs)}")
            print(f"      vs Spin  → avg: {sum(spin_srs)/len(spin_srs):.1f}, "
                  f"min: {min(spin_srs):.1f}, max: {max(spin_srs):.1f}, n={len(spin_srs)}")

        # Unique players with matchup data
        unique_matchup_pids = set(r["Player_ID"] for r in matchup_rows)
        print(f"\n   🏏 Players with matchup data: {len(unique_matchup_pids)}")

    print("\n" + "=" * 65)
    print("  ✅ Phase 2 complete — real data + matchups")
    print("=" * 65)


if __name__ == "__main__":
    main()
