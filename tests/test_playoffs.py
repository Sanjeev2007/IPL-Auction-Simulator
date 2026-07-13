"""The dynamic, N-aware tournament: playoffs must scale to any team count."""
import pytest

from src.simulation.league_engine import simulate_season
from tests.conftest import make_teams

EXPECTED_PLAYOFF_KEYS = {
    2: {"Final"},
    3: {"Eliminator", "Final"},
    4: {"Q1", "Eliminator", "Q2", "Final"},
    6: {"Q1", "Eliminator", "Q2", "Final"},
    8: {"Q1", "Eliminator", "Q2", "Final"},
}


@pytest.mark.parametrize("n", [2, 3, 4, 6, 8])
def test_season_runs_for_any_team_count(players, n):
    teams = make_teams(players, n)
    result = simulate_season(teams)

    # Every team has a standings row and someone wins.
    assert len(result.standings) == n
    assert result.champion is not None

    # Double round-robin => each of the n*(n-1)/2 pairs plays twice.
    assert len(result.league_results) == n * (n - 1)

    # Playoff bracket matches the team count (the N<4 guard).
    assert set(result.playoff_results.keys()) == EXPECTED_PLAYOFF_KEYS[n]


@pytest.mark.parametrize("n", [2, 4, 6])
def test_league_points_are_conserved(players, n):
    """Each league match distributes exactly 2 points (2-0 win or 1-1 tie)."""
    result = simulate_season(teams=make_teams(players, n))
    total_points = sum(row.points for row in result.standings)
    assert total_points == 2 * len(result.league_results)
