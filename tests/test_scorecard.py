"""A simulated match must produce an internally consistent scorecard."""
from src.simulation.match_engine import MatchEngine
from tests.conftest import make_teams


def _check_innings(inn):
    # Physical bounds of a T20 innings.
    assert 0 <= inn.wickets <= 10
    assert 0 <= inn.balls_bowled <= 120
    assert inn.score >= 0

    # Team score is batters' runs + extras, so batter runs can't exceed it.
    batter_runs = sum(bs.runs for bs in inn.batter_scorecards.values())
    assert batter_runs <= inn.score

    # Wickets credited to bowlers can't exceed total wickets (run-outs aren't).
    bowler_wickets = sum(bf.wickets for bf in inn.bowler_figures.values())
    assert bowler_wickets <= inn.wickets

    # No batter faced more balls than were legally bowled.
    for bs in inn.batter_scorecards.values():
        assert bs.balls_faced <= inn.balls_bowled


def test_match_scorecard_is_consistent(players):
    t1, t2 = make_teams(players, 2)
    result = MatchEngine(t1, t2, match_id="TEST").simulate()

    assert result.innings_1 is not None
    _check_innings(result.innings_1)
    if result.innings_2 is not None:
        _check_innings(result.innings_2)

    # A completed match has a winner or is explicitly a tie.
    assert result.winner is not None or result.margin.lower() == "tie"
