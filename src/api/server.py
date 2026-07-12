"""
API Server — Phase 6

Exposes tournament analytics and match simulation via REST endpoints.
Run with: uvicorn src.api.server:app --reload
"""

import os
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from src.analytics.player_analytics import PlayerAnalytics
from src.analytics.team_analytics import TeamAnalytics
from src.models.match_state import MatchResult
from src.simulation.match_engine import MatchEngine
import config

# Initialize Analytics
player_analytics = PlayerAnalytics()
team_analytics = TeamAnalytics()

app = FastAPI(title="IPL Auction Simulator API", version="1.0")

# ---------------------------------------------------------------------------
# CORS — allow the browser frontend to call the API.
# Default allows the Next.js dev server (http://localhost:3000). Override /
# extend via the CORS_ORIGINS env var (comma-separated list of origins).
# ---------------------------------------------------------------------------
_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
_cors_origins = [
    o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MatchRequest(BaseModel):
    team1_id: str
    team2_id: str


@app.get("/api/points_table")
def get_points_table():
    """Returns the simulated average points table."""
    teams = team_analytics.get_all_teams()
    # Sort by average points descending
    teams_sorted = sorted(teams, key=lambda x: x.get("average_points", 0), reverse=True)
    
    table = []
    for i, t in enumerate(teams_sorted, 1):
        table.append({
            "rank": i,
            "team_id": t["team_id"],
            "team_name": t["team_name"],
            "average_points": getattr(t, "average_points", t.get("average_points", 0)),
            "playoff_probability": getattr(t, "playoff_probability", t.get("playoff_probability", 0))
        })
    return {"points_table": table}


@app.get("/api/team_stats")
def get_team_stats():
    """Returns team strengths and overall stats."""
    return {"teams": team_analytics.get_all_teams()}


@app.get("/api/player_stats")
def get_player_stats(limit: int = 10):
    """Returns various top player leaderboards."""
    return {
        "top_batters": player_analytics.get_top_batters(limit),
        "top_bowlers": player_analytics.get_top_bowlers(limit),
        "best_death_batters": player_analytics.get_best_death_batters(limit),
        "best_powerplay_bowlers": player_analytics.get_best_powerplay_bowlers(limit),
        "best_allrounders": player_analytics.get_best_allrounders(limit)
    }


@app.get("/api/championship_odds")
def get_championship_odds():
    """Returns probability of winning the tournament."""
    odds = team_analytics.get_tournament_odds()
    res = []
    for t in odds:
        res.append({
            "team_id": t["team_id"],
            "team_name": t["team_name"],
            "championship_probability": t["championship_probability"],
            "finals_probability": t["finals_probability"]
        })
    return {"odds": res}


# Helper for Match Simulation API
def _get_team_for_match(team_id: str):
    from scripts.run_tournament import load_players, load_teams
    players = load_players()
    teams = load_teams(players)
    for t in teams:
        if t.team_id == team_id:
            return t
    return None


@app.post("/api/simulate_match")
def simulate_match(req: MatchRequest):
    """Simulates a match and returns the scorecard."""
    t1 = _get_team_for_match(req.team1_id)
    t2 = _get_team_for_match(req.team2_id)
    if not t1 or not t2:
        raise HTTPException(status_code=404, detail="Team not found. Use valid team IDs like CSK, MI.")
    
    engine = MatchEngine(t1, t2, match_id="API_MATCH")
    result = engine.simulate()
    
    return _format_match_result(result)


@app.get("/api/scorecard")
def get_scorecard():
    """Simulates a random match and returns its scorecard (for easy testing)."""
    from scripts.run_tournament import load_players, load_teams
    players = load_players()
    teams = load_teams(players)
    t1, t2 = random.sample(teams, 2)
    
    engine = MatchEngine(t1, t2, match_id="RANDOM_API_MATCH")
    result = engine.simulate()
    
    return _format_match_result(result)


def _format_match_result(result: MatchResult) -> dict:
    """Helper to serialize a generic MatchResult to an API response format."""
    
    def format_innings(inn):
        if not inn: return None
        return {
            "batting_team": inn.batting_team.team_id,
            "bowling_team": inn.bowling_team.team_id,
            "score": inn.score,
            "wickets": inn.wickets,
            "overs_completed": inn.overs_completed,
            "batter_scorecards": [
                {
                    "name": sc.name,
                    "runs": sc.runs,
                    "balls_faced": sc.balls_faced,
                    "fours": sc.fours,
                    "sixes": sc.sixes,
                    "strike_rate": round(sc.strike_rate, 1),
                    "dismissal": sc.dismissal_info if sc.is_out else "not out"
                } for sc in inn.batter_scorecards.values() if sc.balls_faced > 0
            ],
            "bowler_figures": [
                {
                    "name": bf.name,
                    "overs": f"{bf.balls_bowled // 6}.{bf.balls_bowled % 6}",
                    "runs_conceded": bf.runs_conceded,
                    "wickets": bf.wickets,
                    "economy": round(bf.economy, 1) if bf.balls_bowled > 0 else 0
                } for bf in inn.bowler_figures.values() if bf.balls_bowled > 0
            ],
            "run_rate_by_over": _calc_run_rate(inn),
            "wicket_timeline": _calc_wicket_timeline(inn)
        }
        
    def _calc_run_rate(inn):
        over_runs = {}
        for b in inn.balls_log:
            if b.over_number not in over_runs:
                over_runs[b.over_number] = 0
            over_runs[b.over_number] += b.runs
        return [{"over": k, "runs": v} for k, v in over_runs.items()]

    def _calc_wicket_timeline(inn):
        wkts = []
        score_at_time = 0
        wkt_count = 0
        for b in inn.balls_log:
            score_at_time += b.runs
            if b.is_wicket:
                wkt_count += 1
                wkts.append({
                    "wicket_number": wkt_count,
                    "over": b.over_number,
                    "ball": b.ball_in_over,
                    "score": score_at_time,
                    "batter_out": b.batter.name if b.batter else "Unknown"
                })
        return wkts
            

    return {
        "match_info": {
            "match_id": result.match_id,
            "team1": result.team_1.team_id,
            "team2": result.team_2.team_id,
            "winner": result.winner.team_id if result.winner else "Tie",
            "margin": result.margin,
            "summary": result.summary()
        },
        "innings1": format_innings(result.innings_1),
        "innings2": format_innings(result.innings_2)
    }
