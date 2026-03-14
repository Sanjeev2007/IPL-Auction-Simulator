"""
Player Analytics Module — Phase 6

Provides aggregations and rankings of players based on derived scores.
"""

import csv
from pathlib import Path

import config
from src.models.player import Role


class PlayerAnalytics:
    def __init__(self):
        self.players = []
        self._load_data()

    def _load_data(self):
        # First load roles and names from master
        master_data = {}
        with open(config.PLAYERS_MASTER_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                master_data[row["Player_ID"]] = {
                    "name": row["Player Name"],
                    "role": Role.from_csv(row["Role"]),
                    "price": row["Base Price Display"]
                }
        
        # Merge with derived scores
        with open(config.DERIVED_SCORES_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pid = row["Player_ID"]
                if pid in master_data:
                    p = {
                        "player_id": pid,
                        "name": master_data[pid]["name"],
                        "role": master_data[pid]["role"].value,
                        "price": master_data[pid]["price"],
                        "bat_rating": float(row["bat_rating"]),
                        "bowl_rating": float(row["bowl_rating"]),
                        "allround_value": float(row["allround_value"]),
                        "overall_rating": float(row["overall_rating"]),
                        "powerplay_rating": float(row["powerplay_rating"]),
                        "death_rating": float(row["death_rating"]),
                    }
                    self.players.append(p)

    def get_top_batters(self, limit: int = 10) -> list[dict]:
        batters = [p for p in self.players if p["role"] in (Role.BATTER.value, Role.WICKETKEEPER.value)]
        batters.sort(key=lambda x: x["bat_rating"], reverse=True)
        return batters[:limit]

    def get_top_bowlers(self, limit: int = 10) -> list[dict]:
        bowlers = [p for p in self.players if p["role"] in (Role.BOWLER_FAST.value, Role.BOWLER_SPIN.value)]
        bowlers.sort(key=lambda x: x["bowl_rating"], reverse=True)
        return bowlers[:limit]

    def get_best_death_batters(self, limit: int = 10) -> list[dict]:
        batters = [p for p in self.players if p["role"] in (Role.BATTER.value, Role.WICKETKEEPER.value, Role.ALL_ROUNDER.value)]
        batters.sort(key=lambda x: x["death_rating"], reverse=True)
        return batters[:limit]

    def get_best_powerplay_bowlers(self, limit: int = 10) -> list[dict]:
        bowlers = [p for p in self.players if p["role"] in (Role.BOWLER_FAST.value, Role.BOWLER_SPIN.value, Role.ALL_ROUNDER.value)]
        bowlers.sort(key=lambda x: x["powerplay_rating"], reverse=True)
        return bowlers[:limit]

    def get_best_allrounders(self, limit: int = 10) -> list[dict]:
        ars = [p for p in self.players if p["role"] == Role.ALL_ROUNDER.value]
        ars.sort(key=lambda x: x["allround_value"], reverse=True)
        return ars[:limit]
