"""
Team Analytics Module — Phase 6

Provides team strengths and tournament probabilities.
"""

import csv
import json
import statistics
from pathlib import Path

import config


class TeamAnalytics:
    def __init__(self):
        self.teams_data = {}
        self._load_data()

    def _load_data(self):
        teams_path = Path(config.DATA_DIR) / "teams" / "team_lineups.json"

        # Map team_id -> full franchise name (e.g. "CSK" -> "Chennai Super Kings")
        team_names = dict(config.IPL_TEAMS)

        # 1. Base initialization from team lineups
        if teams_path.exists():
            with open(teams_path, "r", encoding="utf-8") as f:
                lineups = json.load(f)
                for tid, data in lineups.items():
                    self.teams_data[tid] = {
                        "team_id": tid,
                        "team_name": team_names.get(tid, tid),
                        "playing_xi_pids": data.get("batting_order", [])
                    }

        # 2. Get player scores to compute team strengths
        player_scores = {}
        with open(config.DERIVED_SCORES_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                player_scores[row["Player_ID"]] = {
                    "bat": float(row["bat_rating"]),
                    "bowl": float(row["bowl_rating"]),
                    "ovr": float(row["overall_rating"])
                }

        # Compute average strengths
        for tid, t in self.teams_data.items():
            bat_list = []
            bowl_list = []
            ovr_list = []
            for pid in t["playing_xi_pids"]:
                if pid in player_scores:
                    bat_list.append(player_scores[pid]["bat"])
                    bowl_list.append(player_scores[pid]["bowl"])
                    ovr_list.append(player_scores[pid]["ovr"])
            
            t["batting_strength"] = round(statistics.mean(bat_list), 1) if bat_list else 0.0
            t["bowling_strength"] = round(statistics.mean(bowl_list), 1) if bowl_list else 0.0
            t["overall_strength"] = round(statistics.mean(ovr_list), 1) if ovr_list else 0.0

            # Set defaults for tournament probabilities
            t["championship_probability"] = 0.0
            t["finals_probability"] = 0.0
            t["playoff_probability"] = 0.0
            t["average_points"] = 0.0

        # 3. Load tournament results
        results_path = Path(config.PROJECT_ROOT) / "output" / "tournament_results.csv"
        if results_path.exists():
            with open(results_path, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    tid = row["team_id"]
                    if tid in self.teams_data:
                        self.teams_data[tid]["championship_probability"] = float(row["championship_probability"])
                        self.teams_data[tid]["finals_probability"] = float(row["finals_probability"])
                        self.teams_data[tid]["playoff_probability"] = float(row["playoff_probability"])
                        self.teams_data[tid]["average_points"] = float(row["average_points"])

    def get_all_teams(self) -> list[dict]:
        # Return sorted by overall strength
        teams = list(self.teams_data.values())
        teams.sort(key=lambda x: x["overall_strength"], reverse=True)
        return teams

    def get_team(self, team_id: str) -> dict:
        return self.teams_data.get(team_id)

    def get_tournament_odds(self) -> list[dict]:
        teams = list(self.teams_data.values())
        teams.sort(key=lambda x: x["championship_probability"], reverse=True)
        return teams
