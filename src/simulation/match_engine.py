"""
Match Engine for Phase 4.

Orchestrates a complete T20 match (two innings), returns a MatchResult with scorecards.
"""

from __future__ import annotations

import random
from typing import Optional

from src.models.team import Team
from src.models.match_state import MatchResult
from src.simulation.innings import InningsSimulator


class MatchEngine:
    """Simulates a complete match between two teams."""

    def __init__(self, team1: Team, team2: Team, match_id: str = "M01"):
        self.team1 = team1
        self.team2 = team2
        self.match_id = match_id

    def simulate(self) -> MatchResult:
        # 1. Toss
        teams = [self.team1, self.team2]
        toss_winner = random.choice(teams)
        toss_loser = self.team2 if toss_winner == self.team1 else self.team1
        
        # Simple decision: 50% chance to bat/bowl first
        if random.random() > 0.5:
            bat_first = toss_winner
            bowl_first = toss_loser
        else:
            bat_first = toss_loser
            bowl_first = toss_winner

        # 2. First Innings
        sim1 = InningsSimulator(batting_team=bat_first, bowling_team=bowl_first)
        innings_1 = sim1.simulate()

        # 3. Second Innings
        target = innings_1.score + 1
        sim2 = InningsSimulator(batting_team=bowl_first, bowling_team=bat_first, target=target)
        innings_2 = sim2.simulate()

        # 4. Result determination
        if innings_2.score >= target:
            winner = bowl_first
            wickets_left = 10 - innings_2.wickets
            margin = f"{wickets_left} wickets"
        elif innings_1.score > innings_2.score:
            winner = bat_first
            runs_diff = innings_1.score - innings_2.score
            margin = f"{runs_diff} runs"
        else:
            winner = None  # Super over not implemented, tie
            margin = "Tie"

        # Simple Player of the Match logic: Highest overall bat/bowl contribution
        # To keep it simple, just pick the top scorer from the winning team
        pom = None
        if winner:
            win_innings = innings_1 if winner == bat_first else innings_2
            best_batter_id = None
            best_runs = -1
            for pid, sc in win_innings.batter_scorecards.items():
                if sc.runs > best_runs:
                    best_runs = sc.runs
                    best_batter_id = pid
            
            # Find the player object
            for p in winner.playing_xi:
                if p.player_id == best_batter_id:
                    pom = p
                    break

        result = MatchResult(
            match_id=self.match_id,
            team_1=self.team1,
            team_2=self.team2,
            innings_1=innings_1,
            innings_2=innings_2,
            winner=winner,
            margin=margin,
            player_of_match=pom
        )
        return result
