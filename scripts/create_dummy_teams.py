#!/usr/bin/env python3
"""
Create dummy team lineups for the Match Simulator.
Generates a `team_lineups.json` file containing 6 teams with 11 players each.
"""

import csv
import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENRICHED_DATA_DIR = PROJECT_ROOT / "data" / "enriched"
TEAMS_DATA_DIR = PROJECT_ROOT / "data" / "teams"


def main():
    TEAMS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load players by role
    players_by_role = {"Batsmen": [], "Wicketkeepers": [], "All Rounders": [], "Fast Bowlers": [], "Spinners": []}
    
    master_path = ENRICHED_DATA_DIR / "players_master.csv"
    with open(master_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            role = row["Role"]
            if role in players_by_role:
                players_by_role[role].append(row["Player_ID"])
                
    # Shuffle for randomness
    for role in players_by_role:
        random.shuffle(players_by_role[role])

    teams_config = [
        {"id": "CSK", "name": "Chennai Super Kings"},
        {"id": "MI", "name": "Mumbai Indians"},
        {"id": "RCB", "name": "Royal Challengers Bengaluru"},
        {"id": "KKR", "name": "Kolkata Knight Riders"},
        {"id": "SRH", "name": "Sunrisers Hyderabad"},
        {"id": "RR", "name": "Rajasthan Royals"},
    ]

    team_lineups = {}

    for tm in teams_config:
        # Playing XI composition: 4 Batsmen, 1 WK, 2 All Rounders, 3 Fast Bowlers, 1 Spinner
        batters = []
        batters.extend([players_by_role["Batsmen"].pop() for _ in range(4)])
        batters.extend([players_by_role["Wicketkeepers"].pop() for _ in range(1)])
        
        ars = []
        ars.extend([players_by_role["All Rounders"].pop() for _ in range(2)])
        
        bowlers = []
        bowlers.extend([players_by_role["Fast Bowlers"].pop() for _ in range(3)])
        bowlers.extend([players_by_role["Spinners"].pop() for _ in range(1)])
        
        # batting order mapping
        batting_order = batters + ars + bowlers
        
        # bowlers list mapping
        bowling_plan = bowlers + ars
        
        team_lineups[tm["id"]] = {
            "batting_order": batting_order,
            "bowlers": bowling_plan
        }

    out_path = TEAMS_DATA_DIR / "team_lineups.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(team_lineups, f, indent=4)
        
    print(f"✅ Created 6 teams with playing XIs in {out_path}")

if __name__ == "__main__":
    main()
