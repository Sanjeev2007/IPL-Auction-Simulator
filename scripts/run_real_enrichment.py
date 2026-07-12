#!/usr/bin/env python3
"""
Default enrichment pipeline: REAL Cricsheet data → player ratings.

Ingests Cricsheet ball-by-ball JSON (data/cricsheet/), matches players to
players_master, computes real batting/bowling/phase/matchup/recent-form
statistics, and derives player ratings (derived_scores.csv).

This is the DEFAULT and only supported enrichment path. It does NOT use the
md5-hash synthetic stat generator (src/enrichment/stat_generator.py) — every
number written here traces back to real deliveries. Players without enough
real data are written with data_source="none" and zeroed stats rather than
invented values.

Outputs (data/enriched/):
    ipl_stats_5y.csv        real IPL stats (+ phase splits)
    other_t20_stats_5y.csv  real T20I/BBL/CPL/PSL stats
    player_matchups.csv     real vs-pace / vs-spin splits
    recent_form_12m.csv     real trailing-12-month form
    news_sentiment.csv      neutral placeholder (see write_news_sentiment)
    derived_scores.csv      final 0–100 ratings computed from the above

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
from src.rating.rating_model import RatingEngine

CRICSHEET_DIR = config.DATA_DIR / "cricsheet"


def load_master_ids() -> list[dict]:
    """Load all players from players_master.csv."""
    with open(config.PLAYERS_MASTER_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_ipl_stats(extractor: RealStatExtractor, all_players: list[dict]) -> int:
    """Write ipl_stats_5y.csv from real data only (no synthetic fallback)."""
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
    none_count = 0

    path = config.ENRICHED_DATA_DIR / "ipl_stats_5y.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for p in all_players:
            pid = p["Player_ID"]

            if pid in real_stats and real_stats[pid].get("matches", 0) >= 3:
                row = dict(real_stats[pid])
                row["data_source"] = "real"
                real_count += 1
            else:
                # No synthetic invention: write a zeroed "none" row.
                row = {"Player_ID": pid, "data_source": "none"}
                none_count += 1

            writer.writerow({k: row.get(k, 0) for k in fieldnames})

    print(f"   ✅ ipl_stats_5y.csv: {real_count} real, {none_count} no-data")
    return real_count


def write_other_t20_stats(extractor: RealStatExtractor, all_players: list[dict]) -> int:
    """Write other_t20_stats_5y.csv from real data only."""
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

        for row in real_rows:
            row["data_source"] = "real"
            writer.writerow({k: row.get(k, 0) for k in fieldnames})

        # Players with no real T20 data get a single zeroed "none" row.
        none_count = 0
        for p in all_players:
            pid = p["Player_ID"]
            if pid not in real_pids:
                none_row = {k: 0 for k in fieldnames}
                none_row.update({"Player_ID": pid, "data_source": "none",
                                 "league": "none"})
                writer.writerow(none_row)
                none_count += 1

    print(f"   ✅ other_t20_stats_5y.csv: {len(real_pids)} real, {none_count} no-data")
    return len(real_pids)


def write_recent_form(extractor: RealStatExtractor, all_players: list[dict]) -> int:
    """Write recent_form_12m.csv from real trailing-12-month deliveries."""
    fieldnames = [
        "Player_ID", "matches_12m", "runs_12m", "avg_12m",
        "sr_12m", "wickets_12m", "econ_12m",
    ]

    real_rows = {r["Player_ID"]: r for r in extractor.get_recent_form()}

    path = config.ENRICHED_DATA_DIR / "recent_form_12m.csv"
    real_count = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in all_players:
            pid = p["Player_ID"]
            if pid in real_rows:
                writer.writerow({k: real_rows[pid].get(k, 0) for k in fieldnames})
                real_count += 1
            else:
                zero_row = {k: 0 for k in fieldnames}
                zero_row["Player_ID"] = pid  # zeroed — no recent data
                writer.writerow(zero_row)

    print(f"   ✅ recent_form_12m.csv: {real_count} with real 12m form "
          f"(cutoff {extractor.recent_cutoff})")
    return real_count


def write_news_sentiment(all_players: list[dict]) -> int:
    """Write a NEUTRAL news_sentiment.csv placeholder.

    There is no real news/sentiment feed in this project. The former values
    were md5-seeded template strings masquerading as "real-time sentiment",
    so that headline feature is retired here: every player gets an identical
    neutral row. Because it is constant across players it does not skew the
    (real-data-driven) ratings. The file is kept only so the ratings schema
    and any downstream reader stay intact — it must NOT be presented as real
    or real-time sentiment.
    """
    fieldnames = ["Player_ID", "injury_risk", "sentiment_score", "news_summary"]
    path = config.ENRICHED_DATA_DIR / "news_sentiment.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in all_players:
            writer.writerow({
                "Player_ID": p["Player_ID"],
                "injury_risk": "Unknown",
                "sentiment_score": 50,          # neutral constant — not a signal
                "news_summary": "",
            })
    print(f"   ✅ news_sentiment.csv: {len(all_players)} neutral placeholders "
          f"(synthetic sentiment retired)")
    return len(all_players)


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


def compute_ratings() -> RatingEngine:
    """Run the rating engine over the freshly written enriched CSVs."""
    engine = RatingEngine(config.ENRICHED_DATA_DIR)
    engine.load_data()
    engine.compute_ratings()
    engine.write_csv()
    return engine


def print_top10(engine: RatingEngine, names: dict, roles: dict) -> None:
    """Sanity check: top-10 players by overall rating."""
    ranked = sorted(engine.results, key=lambda r: r["overall_rating"], reverse=True)
    print("\n" + "─" * 65)
    print("  🏆 Top 10 players by overall rating (sanity check)")
    print("─" * 65)
    print(f"   {'Rank':>4}  {'Player':<24} {'Role':<14} "
          f"{'Bat':>5} {'Bowl':>5} {'Overall':>7}")
    for i, r in enumerate(ranked[:10], 1):
        pid = r["Player_ID"]
        print(f"   {i:>4}  {names.get(pid, pid)[:22]:<24} "
              f"{roles.get(pid, '?'):<14} "
              f"{r['bat_rating']:>5.1f} {r['bowl_rating']:>5.1f} "
              f"{r['overall_rating']:>7.1f}")


def main():
    print("=" * 65)
    print("  IPL Auction Simulator — Real Cricsheet Enrichment (default)")
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

    # 7. Write enriched CSVs (all real; no synthetic generator)
    print("\n   📝 Writing enriched datasets (real data only)...")
    ipl_real = write_ipl_stats(extractor, all_players)
    t20_real = write_other_t20_stats(extractor, all_players)
    matchup_count = write_player_matchups(extractor)
    form_real = write_recent_form(extractor, all_players)
    write_news_sentiment(all_players)

    # 8. Derive ratings from the real enriched data
    print("\n   🧮 Deriving player ratings → derived_scores.csv ...")
    engine = compute_ratings()
    print(f"   ✅ derived_scores.csv: {len(engine.results)} rated players")

    # 9. Summary
    print("\n" + "=" * 65)
    print("  📊 Pipeline Summary")
    print("=" * 65)
    matches_in_window = len(set(
        d.match_id for d in deliveries if d.date >= extractor.cutoff_date
    ))
    print(f"   Matches processed (5y): {matches_in_window}")
    print(f"   Deliveries processed:   {extractor.total_deliveries}")
    print(f"   Players with real data: {len(real_pids)} / {len(all_players)} "
          f"({len(real_pids)/len(all_players)*100:.0f}%)")
    print(f"   IPL stats (real):       {ipl_real}")
    print(f"   T20 stats (real):       {t20_real}")
    print(f"   Recent-form (real 12m): {form_real}")
    print(f"   Matchup entries:        {matchup_count}")
    print(f"   Ratings written:        {len(engine.results)}")

    # 10. Sanity check — top 10 by overall rating
    names, roles = {}, {}
    with open(config.PLAYERS_MASTER_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            names[row["Player_ID"]] = row["Player Name"]
            roles[row["Player_ID"]] = row["Role"]
    print_top10(engine, names, roles)

    print("\n" + "=" * 65)
    print("  ✅ Real enrichment complete — ratings derived from Cricsheet data")
    print("=" * 65)


if __name__ == "__main__":
    main()
