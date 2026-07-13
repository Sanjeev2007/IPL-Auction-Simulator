"""Shared test fixtures. Makes `src` / `scripts` importable and builds test teams."""
import sys
import random
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402
from scripts.run_tournament import load_players, build_teams  # noqa: E402


@pytest.fixture(scope="session")
def players():
    return load_players()


@pytest.fixture(autouse=True)
def _seed():
    """Deterministic RNG per test so stochastic sims are reproducible."""
    random.seed(1234)


def make_teams(players, n):
    """Build `n` valid teams by chunking the player pool into XIs of 11."""
    pids = list(players.keys())
    assert n * 11 <= len(pids), "not enough players for that many teams"
    roster = {}
    for i in range(n):
        chunk = pids[i * 11:(i + 1) * 11]
        roster[f"T{i + 1}"] = {"batting_order": chunk, "bowlers": chunk[:6], "name": f"Team {i + 1}"}
    return build_teams(players, roster)
