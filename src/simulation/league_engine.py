"""
League & Tournament Engine — Phase 5

Implements:
  - Double round-robin schedule generation (30 matches for 6 teams)
  - Standings tracking with NRR
  - IPL-style playoffs (Q1, Eliminator, Q2, Final)
  - Multi-season simulation with aggregate analytics
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Optional

from src.models.team import Team
from src.models.match_state import MatchResult
from src.simulation.match_engine import MatchEngine


# ---------------------------------------------------------------------------
# Standings Row
# ---------------------------------------------------------------------------

@dataclass
class StandingsRow:
    """Tracks a single team's season statistics."""
    team: Team
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    points: int = 0
    runs_scored: int = 0
    runs_conceded: int = 0
    overs_faced: float = 0.0    # decimal overs (e.g. 20.0)
    overs_bowled: float = 0.0   # decimal overs

    @property
    def nrr(self) -> float:
        if self.overs_faced == 0 or self.overs_bowled == 0:
            return 0.0
        return (self.runs_scored / self.overs_faced) - (self.runs_conceded / self.overs_bowled)


# ---------------------------------------------------------------------------
# Season Result
# ---------------------------------------------------------------------------

@dataclass
class SeasonResult:
    standings: list[StandingsRow]
    league_results: list[MatchResult]
    playoff_results: dict[str, MatchResult]   # Q1, Eliminator, Q2, Final
    champion: Optional[Team] = None
    runner_up: Optional[Team] = None
    playoff_teams: list[Team] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def generate_schedule(teams: list[Team]) -> list[tuple[Team, Team]]:
    """Generate double round-robin schedule (each pair plays twice)."""
    fixtures = []
    for t1, t2 in itertools.combinations(teams, 2):
        fixtures.append((t1, t2))
        fixtures.append((t2, t1))   # reverse fixture
    random.shuffle(fixtures)
    return fixtures


def _update_standings(standings: dict[str, StandingsRow], result: MatchResult) -> None:
    """Update standings after a match result."""
    inn1 = result.innings_1
    inn2 = result.innings_2
    if not inn1 or not inn2:
        return

    # Determine which team batted first / second
    bat_first_id = inn1.batting_team.team_id
    bat_second_id = inn2.batting_team.team_id

    # Update batting-first team
    s1 = standings[bat_first_id]
    s1.matches_played += 1
    s1.runs_scored += inn1.score
    s1.overs_faced += inn1.overs_decimal
    s1.runs_conceded += inn2.score
    s1.overs_bowled += inn2.overs_decimal

    # Update batting-second team
    s2 = standings[bat_second_id]
    s2.matches_played += 1
    s2.runs_scored += inn2.score
    s2.overs_faced += inn2.overs_decimal
    s2.runs_conceded += inn1.score
    s2.overs_bowled += inn1.overs_decimal

    # Points
    if result.winner:
        winner_id = result.winner.team_id
        loser_id = bat_second_id if winner_id == bat_first_id else bat_first_id
        standings[winner_id].wins += 1
        standings[winner_id].points += 2
        standings[loser_id].losses += 1
    else:
        # Tie — 1 point each (rare)
        s1.points += 1
        s2.points += 1


def _rank_standings(standings: dict[str, StandingsRow]) -> list[StandingsRow]:
    """Sort by points (desc), then NRR (desc)."""
    return sorted(standings.values(), key=lambda s: (s.points, s.nrr), reverse=True)


def simulate_season(teams: list[Team], verbose: bool = False) -> SeasonResult:
    """Simulate one full IPL-style season: league + playoffs."""

    # --- League Stage ---
    schedule = generate_schedule(teams)
    standings = {t.team_id: StandingsRow(team=t) for t in teams}
    league_results = []

    for i, (t1, t2) in enumerate(schedule, 1):
        engine = MatchEngine(t1, t2, match_id=f"L{i:02d}")
        result = engine.simulate()
        league_results.append(result)
        _update_standings(standings, result)

        if verbose:
            winner_name = result.winner.name if result.winner else "Tie"
            print(f"   Match {i:2d}: {t1.team_id} vs {t2.team_id} → {winner_name} ({result.margin})")

    ranked = _rank_standings(standings)

    if verbose:
        print("\n   ── Points Table ──")
        print(f"   {'#':>2} {'Team':<6} {'M':>3} {'W':>3} {'L':>3} {'Pts':>4} {'NRR':>7}")
        for i, s in enumerate(ranked, 1):
            print(f"   {i:>2} {s.team.team_id:<6} {s.matches_played:>3} {s.wins:>3} "
                  f"{s.losses:>3} {s.points:>4} {s.nrr:>+7.3f}")

    # --- Playoffs ---
    # The bracket scales to the number of teams (dynamic team counts):
    #   >= 4 teams → full IPL playoff (Q1, Eliminator, Q2, Final)
    #      3 teams → Eliminator (rank 2 vs rank 3), then Final vs rank 1
    #      2 teams → straight Final (rank 1 vs rank 2)
    #      1 team  → sole team is champion by default (no match)
    n = len(ranked)
    playoff_seeds = [s.team for s in ranked[: min(n, 4)]]
    playoff_results: dict[str, MatchResult] = {}
    champion: Optional[Team] = None
    runner_up: Optional[Team] = None

    if n >= 4:
        top4 = playoff_seeds

        # Qualifier 1: Rank 1 vs Rank 2
        q1 = MatchEngine(top4[0], top4[1], match_id="Q1").simulate()
        playoff_results["Q1"] = q1
        q1_winner = q1.winner or top4[0]
        q1_loser = top4[1] if q1_winner.team_id == top4[0].team_id else top4[0]

        # Eliminator: Rank 3 vs Rank 4
        elim = MatchEngine(top4[2], top4[3], match_id="EL").simulate()
        playoff_results["Eliminator"] = elim
        elim_winner = elim.winner or top4[2]

        # Qualifier 2: Q1 loser vs Eliminator winner
        q2 = MatchEngine(q1_loser, elim_winner, match_id="Q2").simulate()
        playoff_results["Q2"] = q2
        q2_winner = q2.winner or q1_loser

        # Final
        final = MatchEngine(q1_winner, q2_winner, match_id="FN").simulate()
        playoff_results["Final"] = final
        champion = final.winner or q1_winner
        runner_up = q2_winner if champion.team_id == q1_winner.team_id else q1_winner

    elif n == 3:
        r1, r2, r3 = ranked[0].team, ranked[1].team, ranked[2].team

        # Eliminator: Rank 2 vs Rank 3
        elim = MatchEngine(r2, r3, match_id="EL").simulate()
        playoff_results["Eliminator"] = elim
        elim_winner = elim.winner or r2

        # Final: Rank 1 vs Eliminator winner
        final = MatchEngine(r1, elim_winner, match_id="FN").simulate()
        playoff_results["Final"] = final
        champion = final.winner or r1
        runner_up = elim_winner if champion.team_id == r1.team_id else r1

    elif n == 2:
        r1, r2 = ranked[0].team, ranked[1].team

        # Straight Final: Rank 1 vs Rank 2
        final = MatchEngine(r1, r2, match_id="FN").simulate()
        playoff_results["Final"] = final
        champion = final.winner or r1
        runner_up = r2 if champion.team_id == r1.team_id else r1

    elif n == 1:
        # Only one team — champion by default, no match played.
        champion = ranked[0].team

    if verbose:
        print(f"\n   ── Playoffs ──")
        for label in ("Q1", "Eliminator", "Q2", "Final"):
            m = playoff_results.get(label)
            if m:
                winner = m.winner.team_id if m.winner else "Tie"
                print(f"   {label + ':':<11} {m.team_1.team_id} vs {m.team_2.team_id} → {winner}")
        if champion:
            print(f"\n   🏆 CHAMPION: {champion.name}")

    return SeasonResult(
        standings=ranked,
        league_results=league_results,
        playoff_results=playoff_results,
        champion=champion,
        runner_up=runner_up,
        playoff_teams=playoff_seeds,
    )


def simulate_multiple_seasons(teams: list[Team], n: int = 500) -> dict[str, dict]:
    """
    Run n seasons and aggregate analytics per team.

    Returns: {team_id: {championships, finals, playoffs, total_points, seasons}}
    """
    agg: dict[str, dict] = {}
    for t in teams:
        agg[t.team_id] = {
            "team_name": t.name,
            "championships": 0,
            "finals": 0,
            "playoffs": 0,
            "total_points": 0,
            "seasons": n,
        }

    for i in range(1, n + 1):
        result = simulate_season(teams)

        # Aggregate league points
        for s in result.standings:
            agg[s.team.team_id]["total_points"] += s.points

        # Playoffs
        for t in result.playoff_teams:
            agg[t.team_id]["playoffs"] += 1

        # Finalists
        if result.champion:
            agg[result.champion.team_id]["championships"] += 1
            agg[result.champion.team_id]["finals"] += 1
        if result.runner_up:
            agg[result.runner_up.team_id]["finals"] += 1

        if i % 100 == 0:
            print(f"   ... {i}/{n} seasons complete")

    # Compute probabilities
    for tid, d in agg.items():
        d["championship_probability"] = round(d["championships"] / n * 100, 1)
        d["finals_probability"] = round(d["finals"] / n * 100, 1)
        d["playoff_probability"] = round(d["playoffs"] / n * 100, 1)
        d["average_points"] = round(d["total_points"] / n, 1)

    return agg
