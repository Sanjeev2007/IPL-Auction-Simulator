"""
Innings Simulation Engine for Phase 4.

Handles the ball-by-ball simulation of a single innings, including batter rotation,
bowler rotation, chase logic, and probability distribution resolution.
"""

from __future__ import annotations

import random
from typing import Optional

from src.models.player import Player, Role
from src.models.team import Team
from src.models.match_state import InningsState, BallOutcome, BatterScorecard, BowlerFigures


# Base probabilities based on historical T20 data
BASE_PROBS = {
    # Phase: (DOT, SINGLE, DOUBLE, TRIPLE, FOUR, SIX, WICKET)
    "powerplay": (0.40, 0.25, 0.05, 0.01, 0.15, 0.06, 0.08),
    "middle":    (0.32, 0.40, 0.08, 0.01, 0.09, 0.05, 0.05),
    "death":     (0.28, 0.22, 0.08, 0.01, 0.14, 0.15, 0.12),
}

OUTCOME_TYPES = ["DOT", "SINGLE", "DOUBLE", "TRIPLE", "FOUR", "SIX", "WICKET"]
RUNS_MAP = {"DOT": 0, "SINGLE": 1, "DOUBLE": 2, "TRIPLE": 3, "FOUR": 4, "SIX": 6, "WICKET": 0}


class InningsSimulator:
    """Simulates a complete T20 innings ball-by-ball."""

    def __init__(self, batting_team: Team, bowling_team: Team, target: Optional[int] = None):
        self.state = InningsState(batting_team=batting_team, bowling_team=bowling_team, target=target)
        
        # Use manually provided batting order
        self.batting_order = self.state.batting_team.batting_order
        
        # Use manually provided bowlers list
        self.bowlers = [p for p, overs in self.state.bowling_team.bowling_plan]
        
        if not self.batting_order or len(self.batting_order) != 11:
            raise ValueError(f"Team {self.state.batting_team.name} requires exactly 11 players in batting_order")
        if not self.bowlers:
            raise ValueError(f"Team {self.state.bowling_team.name} requires at least 1 bowler in bowling_plan")
        
        self.state.striker_id = self.batting_order[0].player_id
        self.state.non_striker_id = self.batting_order[1].player_id
        self.state.next_batter_index = 2
        
        # Init scorecards
        for p in self.batting_order:
            self.state.batter_scorecards[p.player_id] = BatterScorecard(player_id=p.player_id, name=p.name)
        for b in self.bowlers:
            self.state.bowler_figures[b.player_id] = BowlerFigures(player_id=b.player_id, name=b.name)

    def _get_bowler_for_over(self, over_number: int) -> Player:
        # Simple rotation through the provided bowlers list
        idx = (over_number - 1) % len(self.bowlers)
        return self.bowlers[idx]

    def _get_player_by_id(self, team: Team, pid: str) -> Player:
        for p in team.playing_xi:
            if p.player_id == pid:
                return p
        return team.playing_xi[0]

    def _calculate_probabilities(self, striker: Player, bowler: Player, phase: str) -> list[float]:
        """Calculate adjusted probabilities based on phase, ratings, and match context."""
        base = list(BASE_PROBS[phase])
        
        # Rating modifiers (scale ratings roughly from 0.5 to 1.5)
        # A bat_rating of 80 → ~1.3 multiplier for positive outcomes
        bat_mod = 0.5 + (striker.bat_rating / 100.0)
        bowl_mod = 0.5 + (bowler.bowl_rating / 100.0)
        
        # Matchup modifiers (simplistic check vs Spin)
        is_spin = bowler.role == Role.BOWLER_SPIN or (bowler.role == Role.ALL_ROUNDER and "spin" in str(bowler.bowling_style).lower())
        
        # Adjust probabilities
        # Dots & Wickets favor bowler
        # Boundaries favor batter
        adj = [0.0] * 7
        
        # DOT
        adj[0] = base[0] * bowl_mod / bat_mod
        # SINGLE, DOUBLE, TRIPLE (neutral-ish, slightly favor batter focus)
        adj[1] = base[1] * bat_mod * 0.9
        adj[2] = base[2] * bat_mod
        adj[3] = base[3] * bat_mod
        # FOUR, SIX (heavy batter favor)
        adj[4] = base[4] * (bat_mod ** 1.5) / (bowl_mod ** 0.5)
        adj[5] = base[5] * (bat_mod ** 1.8) / (bowl_mod ** 0.8)
        # WICKET (heavy bowler favor)
        adj[6] = base[6] * (bowl_mod ** 1.5) / (bat_mod ** 0.8)

        # Chase Logic (Bazball mode)
        if self.state.target:
            balls_left = 120 - self.state.balls_bowled
            runs_needed = self.state.target - self.state.score
            if balls_left > 0:
                req_rr = (runs_needed / balls_left) * 6
                # If required RR is high (> 10), batters swing harder -> more 6s, 4s AND Wickets
                if req_rr > 10.0:
                    pressure_factor = min(req_rr / 10.0, 2.0)  # max 2x multiplier
                    adj[4] *= (pressure_factor * 1.1)
                    adj[5] *= (pressure_factor * 1.3)
                    adj[6] *= (pressure_factor * 1.2)
                    adj[0] *= 0.8 # fewer dots
        
        # Normalize to 1.0
        total = sum(adj)
        return [p / total for p in adj]

    def _swap_strikers(self):
        self.state.striker_id, self.state.non_striker_id = self.state.non_striker_id, self.state.striker_id

    def simulate(self) -> InningsState:
        """Run the simulation loop."""
        for over in range(1, 21):
            if self.state.is_complete:
                break
                
            bowler = self._get_bowler_for_over(over)
            self.state.current_bowler_id = bowler.player_id
            
            for ball_idx in range(1, 7):
                if self.state.is_complete:
                    break
                    
                striker = self._get_player_by_id(self.state.batting_team, self.state.striker_id)
                phase = self.state.phase
                
                probs = self._calculate_probabilities(striker, bowler, phase)
                outcome_str = random.choices(OUTCOME_TYPES, weights=probs, k=1)[0]
                runs = RUNS_MAP[outcome_str]
                is_wkt = (outcome_str == "WICKET")
                
                # Record ball
                ball = BallOutcome(
                    runs=runs, is_wicket=is_wkt, batter=striker, bowler=bowler,
                    over_number=over, ball_in_over=ball_idx
                )
                self.state.balls_log.append(ball)
                self.state.score += runs
                self.state.balls_bowled += 1
                
                # Update Scorecards
                bc = self.state.batter_scorecards[striker.player_id]
                bc.runs += runs
                bc.balls_faced += 1
                if runs == 4: bc.fours += 1
                elif runs == 6: bc.sixes += 1
                
                bf = self.state.bowler_figures[bowler.player_id]
                bf.runs_conceded += runs
                bf.balls_bowled += 1
                
                if is_wkt:
                    self.state.wickets += 1
                    bc.is_out = True
                    bc.dismissal_info = f"b {bowler.name}"
                    bf.wickets += 1
                    
                    if self.state.wickets < 10:
                        self.state.striker_id = self.batting_order[self.state.next_batter_index].player_id
                        self.state.next_batter_index += 1
                else:
                    if runs % 2 != 0:
                        self._swap_strikers()
                        
            # End of over
            self._swap_strikers()
            
        return self.state
