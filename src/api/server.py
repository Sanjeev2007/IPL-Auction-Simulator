"""
API Server — Phase 6

Exposes tournament analytics and match simulation via REST endpoints.
Run with: uvicorn src.api.server:app --reload
"""

import os
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from src.analytics.player_analytics import PlayerAnalytics
from src.analytics.team_analytics import TeamAnalytics
from src.models.match_state import MatchResult
from src.models.team import Team
from src.simulation.match_engine import MatchEngine
from src.simulation.league_engine import (
    SeasonResult,
    simulate_season,
    simulate_multiple_seasons,
)
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

# ---------------------------------------------------------------------------
# Live auction (Milestone 5) — REST + WebSocket transport for the auction
# state machine in src/auction/. Additive: the static dashboard is untouched.
# ---------------------------------------------------------------------------
from src.api.auction_ws import router as auction_router  # noqa: E402

app.include_router(auction_router)


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


# ---------------------------------------------------------------------------
# Player pool — loaded once and cached. Rosters (from the bundled teams, the
# API, or a future auction) reference these players by ID.
# ---------------------------------------------------------------------------
_player_pool = None


def _load_player_pool():
    global _player_pool
    if _player_pool is None:
        from scripts.run_tournament import load_players
        _player_pool = load_players()
    return _player_pool


# Helper for Match Simulation API
def _get_team_for_match(team_id: str):
    from scripts.run_tournament import load_teams
    teams = load_teams(_load_player_pool())
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
    from scripts.run_tournament import load_teams
    teams = load_teams(_load_player_pool())
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


# ---------------------------------------------------------------------------
# Dynamic-team season simulation
# ---------------------------------------------------------------------------
# Accepts an arbitrary set of teams (their rosters) and simulates a full
# season — league round-robin + a playoff bracket that scales to the team
# count (2 → straight final, 3 → eliminator + final, ≥4 → Q1/EL/Q2/Final).
# This is the foundation the M5 auction feeds drafted rosters into.


class TeamRoster(BaseModel):
    team_id: str
    name: Optional[str] = None
    batting_order: list[str] = Field(..., description="Exactly 11 player IDs, in batting order")
    bowlers: list[str] = Field(..., description="Player IDs eligible to bowl")


class SeasonRequest(BaseModel):
    teams: list[TeamRoster]
    seasons: int = Field(1, ge=1, le=2000, description="Seasons to simulate; >1 returns aggregate odds")


def _team_ref(team: Optional[Team]) -> Optional[dict]:
    if team is None:
        return None
    return {"team_id": team.team_id, "team_name": team.name}


def _serialize_standings(result: SeasonResult) -> list[dict]:
    table = []
    for rank, s in enumerate(result.standings, 1):
        table.append({
            "rank": rank,
            "team_id": s.team.team_id,
            "team_name": s.team.name,
            "matches_played": s.matches_played,
            "wins": s.wins,
            "losses": s.losses,
            "points": s.points,
            "nrr": round(s.nrr, 3),
        })
    return table


@app.post("/api/simulate_season")
def simulate_season_endpoint(req: SeasonRequest):
    """Simulate a full season for a caller-provided set of teams/rosters.

    Supports any number of teams (≥2). With ``seasons > 1`` it also returns
    aggregate championship/playoff odds across the runs.
    """
    from scripts.run_tournament import build_teams

    if len(req.teams) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 teams to simulate a season.")

    team_ids = [t.team_id for t in req.teams]
    if len(set(team_ids)) != len(team_ids):
        raise HTTPException(status_code=400, detail="Team IDs must be unique.")

    roster_data = {
        t.team_id: {
            "batting_order": t.batting_order,
            "bowlers": t.bowlers,
            "name": t.name or t.team_id,
        }
        for t in req.teams
    }

    try:
        teams = build_teams(_load_player_pool(), roster_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Single representative season for standings + a concrete bracket.
    result = simulate_season(teams)

    response = {
        "team_count": len(teams),
        "standings": _serialize_standings(result),
        "playoff_teams": [t.team_id for t in result.playoff_teams],
        "playoffs": {
            label: {
                "team1": m.team_1.team_id,
                "team2": m.team_2.team_id,
                "winner": m.winner.team_id if m.winner else "Tie",
                "margin": m.margin,
                "summary": m.summary(),
            }
            for label, m in result.playoff_results.items()
        },
        "champion": _team_ref(result.champion),
        "runner_up": _team_ref(result.runner_up),
    }

    # Optional: aggregate odds across many seasons.
    if req.seasons > 1:
        agg = simulate_multiple_seasons(teams, n=req.seasons)
        odds = [
            {
                "team_id": tid,
                "team_name": d["team_name"],
                "championship_probability": d["championship_probability"],
                "finals_probability": d["finals_probability"],
                "playoff_probability": d["playoff_probability"],
                "average_points": d["average_points"],
            }
            for tid, d in sorted(
                agg.items(), key=lambda x: x[1]["championship_probability"], reverse=True
            )
        ]
        response["seasons_simulated"] = req.seasons
        response["championship_odds"] = odds

    return response
