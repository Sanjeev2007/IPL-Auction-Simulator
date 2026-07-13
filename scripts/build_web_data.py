"""
Pre-generate the engine's output as static JSON for a backend-free Vercel deploy.

Runs the real simulation engine locally and writes JSON in the exact shapes the
frontend's lib/api.ts already expects, so the deployed site needs no live API:

  web/src/data/team_stats.json        {"teams": [...]}
  web/src/data/championship_odds.json {"odds": [...]}
  web/src/data/points_table.json      {"points_table": [...]}
  web/public/data/matches.json        [ matchResult, ... ]  (pool for all pairings)

Re-run after the engine or data changes, then commit the JSON:
    python scripts/build_web_data.py
"""
import itertools
import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

random.seed(7)

# Championship odds / points table read output/tournament_results.csv — make sure
# it exists and is fresh (500-season aggregate).
print("→ generating tournament aggregate (500 seasons)…")
subprocess.run([sys.executable, "scripts/run_tournament.py"], cwd=ROOT, check=True,
               capture_output=True)

from src.api import server                      # noqa: E402
from src.api.server import MatchRequest         # noqa: E402

SRC = ROOT / "web" / "src" / "data"
PUB = ROOT / "web" / "public" / "data"
SRC.mkdir(parents=True, exist_ok=True)
PUB.mkdir(parents=True, exist_ok=True)


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, separators=(",", ":")))
    print(f"  wrote {path.relative_to(ROOT)}")


# Static tables (used by the server components — imported directly).
dump(SRC / "team_stats.json", server.get_team_stats())
dump(SRC / "championship_odds.json", server.get_championship_odds())
dump(SRC / "points_table.json", server.get_points_table())

# Match pool: every ordered pairing, a couple of variants each, so the Simulator's
# matchup picker always has a real result and re-simulating shows variety.
team_ids = [t["team_id"] for t in server.get_team_stats()["teams"]]
print(f"→ simulating match pool for {len(team_ids)} teams…")
matches = []
for a, b in itertools.permutations(team_ids, 2):
    for _ in range(2):
        matches.append(server.simulate_match(MatchRequest(team1_id=a, team2_id=b)))
random.shuffle(matches)
dump(PUB / "matches.json", matches)

print(f"✓ done — {len(matches)} matches, static data ready for Vercel.")
