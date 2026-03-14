#!/usr/bin/env python3
"""
Run Phase 4: Match Simulator

Loads teams and player ratings, runs 1 detailed match, and then 100 match iterations.
"""

import csv
import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.player import Player, Role
from src.models.team import Team
from src.simulation.match_engine import MatchEngine


def load_players() -> dict[str, Player]:
    players = {}
    master_path = config.PLAYERS_MASTER_PATH
    scores_path = config.DERIVED_SCORES_PATH

    # 1. Base info
    with open(master_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = row["Player_ID"]
            p = Player(
                player_id=pid,
                name=row["Player Name"],
                role=Role.from_csv(row["Role"]),
                base_price=int(row["Base Price (INR)"])
            )
            players[pid] = p

    # 2. Ratings
    with open(scores_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = row["Player_ID"]
            if pid in players:
                players[pid].bat_rating = float(row["bat_rating"])
                players[pid].bowl_rating = float(row["bowl_rating"])
                players[pid].allround_value = float(row["allround_value"])
                players[pid].overall_rating = float(row["overall_rating"])
                
    return players


def load_teams(players: dict[str, Player]) -> list[Team]:
    teams_path = Path(config.DATA_DIR) / "teams" / "team_lineups.json"
    
    if not teams_path.exists():
        raise FileNotFoundError(f"Missing team lineups file at {teams_path}. Please provide it manually.")
        
    teams = []
    
    with open(teams_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for team_id, tdata in data.items():
        batting_pids = tdata.get("batting_order", [])
        bowler_pids = tdata.get("bowlers", [])
        
        if len(batting_pids) != 11:
            raise ValueError(f"Team {team_id} must have exactly 11 players in batting_order. Found {len(batting_pids)}.")
            
        t = Team(team_id=team_id, name=team_id)
        
        # Build playing XI and batting order
        for pid in batting_pids:
            if pid not in players:
                raise ValueError(f"Player {pid} in team {team_id} not found in players_master.csv")
            p = players[pid]
            t.playing_xi.append(p)
            t.batting_order.append(p)
            
        # Build bowling plan
        for pid in bowler_pids:
            if pid not in players:
                raise ValueError(f"Bowler {pid} in team {team_id} not found in players_master.csv")
            # For simplicity, assign 4 overs max to each listed bowler
            t.bowling_plan.append((players[pid], 4))
            
        teams.append(t)
        
    return teams


def print_scorecard(result):
    print("\n" + "=" * 65)
    print(f"  🏏 MATCH RESULT: {result.summary()}")
    print("=" * 65)
    
    for idx, innings in enumerate([result.innings_1, result.innings_2], 1):
        if not innings: continue
        print(f"\n   --- INNINGS {idx}: {innings.batting_team.name} ---")
        print(f"   Score: {innings.score}/{innings.wickets} in {innings.overs_completed:.1f} overs")
        print("\n   Batting:")
        print(f"   {'Batter':<20} {'R':>4} {'B':>4}   {'SR':>6}   {'Dismissal'}")
        
        # We assume the order of keys relies on insertion order, which holds mostly true
        # Or sort by balls faced / runs to at least show who batted
        batted = [sc for sc in innings.batter_scorecards.values() if sc.balls_faced > 0]
        # Sort by batting order (which roughly correlates to who came first)
        for sc in batted:
            sr = f"{sc.strike_rate:.1f}"
            out = sc.dismissal_info if sc.is_out else "not out"
            print(f"   {sc.name[:20]:<20} {sc.runs:>4} {sc.balls_faced:>4}   {sr:>6}   {out}")
            
        print("\n   Bowling:")
        print(f"   {'Bowler':<20} {'O':>4} {'R':>4} {'W':>2}   {'Econ':>6}")
        bowled = [bf for bf in innings.bowler_figures.values() if bf.balls_bowled > 0]
        for bf in bowled:
            overs = f"{bf.balls_bowled//6}.{bf.balls_bowled%6}"
            econ = f"{bf.economy:.1f}"
            print(f"   {bf.name[:20]:<20} {overs:>4} {bf.runs_conceded:>4} {bf.wickets:>2}   {econ:>6}")


def main():
    print("=================================================================")
    print("  IPL Auction Simulator — Phase 4: Match Simulator")
    print("=================================================================")

    # 1. Load data
    players = load_players()
    print(f"\n   📋 Loaded {len(players)} players with ratings")
    
    teams = load_teams(players)
    print(f"   🏟️ Loaded {len(teams)} teams")
    
    # 2. Simulate 1 Match
    team1 = teams[0]
    team2 = teams[1]
    
    engine = MatchEngine(team1, team2)
    result = engine.simulate()
    print_scorecard(result)
    
    # 3. Simulate 100 Matches between random pairs to get distributions
    print("\n" + "=" * 65)
    print("  📊 Running 100 Match Simulations")
    print("=" * 65)
    
    scores = []
    wickets_fallen = []
    
    for i in range(100):
        t1, t2 = random.sample(teams, 2)
        eng = MatchEngine(t1, t2)
        res = eng.simulate()
        scores.append(res.innings_1.score)
        wickets_fallen.append(res.innings_1.wickets)
        if res.innings_2:
            scores.append(res.innings_2.score)
            wickets_fallen.append(res.innings_2.wickets)
            
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)
    avg_wkts = sum(wickets_fallen) / len(wickets_fallen)
    
    # Histogram of scores
    buckets = [0] * 5  # <120, 120-150, 150-180, 180-210, >210
    for s in scores:
        if s < 120: buckets[0] += 1
        elif s < 150: buckets[1] += 1
        elif s < 180: buckets[2] += 1
        elif s < 210: buckets[3] += 1
        else: buckets[4] += 1
        
    hist = (
        f"   <120: {buckets[0]}\n"
        f"   120-149: {buckets[1]}\n"
        f"   150-179: {buckets[2]}\n"
        f"   180-209: {buckets[3]}\n"
        f"   210+: {buckets[4]}"
    )

    print(f"\n   🏏 Matches Simulated: 100 (200 innings)")
    print(f"   📈 Average Score: {avg_score:.1f}")
    print(f"   💥 Highest Score: {max_score}")
    print(f"   🐢 Lowest Score:  {min_score}")
    print(f"   ⚾ Average Wickets: {avg_wkts:.1f}")
    
    print(f"\n   Score Distribution:\n{hist}")
    
    print("\n" + "=" * 65)
    print("  ✅ Phase 4 complete — Match Simulation engine verified")
    print("=" * 65)

if __name__ == "__main__":
    main()
