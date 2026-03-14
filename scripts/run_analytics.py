#!/usr/bin/env python3
"""
Test script for Phase 6 Analytics and API layer.
Loads the modules and prints sample output directly (simulating what the API returns).
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.player_analytics import PlayerAnalytics
from src.analytics.team_analytics import TeamAnalytics
from src.api.server import simulate_match, get_scorecard, MatchRequest

# Set up to print readable JSON
def print_json(data):
    print(json.dumps(data, indent=2))

def main():
    print("=================================================================")
    print("  IPL Auction Simulator — Phase 6: Analytics & API Output Test")
    print("=================================================================\n")

    p_analytics = PlayerAnalytics()
    t_analytics = TeamAnalytics()

    # 1. Player Analytics
    print("── 1. Top 3 Batters ──")
    print_json(p_analytics.get_top_batters(3))

    print("\n── 2. Top 3 Bowlers ──")
    print_json(p_analytics.get_top_bowlers(3))

    print("\n── 3. Best 3 Death Batters ──")
    print_json(p_analytics.get_best_death_batters(3))

    print("\n── 4. Best 3 Powerplay Bowlers ──")
    print_json(p_analytics.get_best_powerplay_bowlers(3))

    print("\n── 5. Best 3 Allrounders ──")
    print_json(p_analytics.get_best_allrounders(3))

    # 2. Team Analytics
    print("\n── 6. Team Strength & Stats (Top 2 by Strategy) ──")
    teams = t_analytics.get_all_teams()
    print_json(teams[:2])

    print("\n── 7. Championship Odds (API format) ──")
    odds = t_analytics.get_tournament_odds()
    print_json([{"team_id": t["team_id"], "champ%": t["championship_probability"]} for t in odds])

    # 3. Match Analytics (Scorecard / timeline mock)
    print("\n── 8. Match Simulation & Analytics Payload (CSK vs MI) ──")
    req = MatchRequest(team1_id="CSK", team2_id="MI")
    res = simulate_match(req)
    
    # Just print the run rate, timeline, and match info to avoid giant output
    print_json(res["match_info"])
    
    print("\n   Run Rate By Over (Innings 1 excerpt):")
    print_json(res["innings1"]["run_rate_by_over"][:5])
    
    print("\n   Wicket Timeline (Innings 1 excerpt):")
    print_json(res["innings1"]["wicket_timeline"][:3])

    print("\n=================================================================")
    print("  ✅ All analytics modules and API formatting successful")
    print("=================================================================")

if __name__ == "__main__":
    main()
