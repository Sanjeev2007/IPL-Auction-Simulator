"""
M7 — engine validation. Compare the simulator's output distributions against
REAL IPL from the Cricsheet data, so we know whether the model is calibrated.

Measures 1st/2nd-innings totals, bat-first win rate, and wickets, for:
  - real IPL (parsed from data/cricsheet/ipl/*.json, full 20-over matches)
  - the simulator (N simulated matches across the real team pool)

Run: python scripts/validate_engine.py
"""
import glob
import json
import random
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
random.seed(11)

from scripts.run_tournament import load_players, load_teams  # noqa: E402
from src.simulation.match_engine import MatchEngine           # noqa: E402


def pctl(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p / 100 * len(xs)))]


def summarize(label, first, second, batfirst_wins, wkts):
    n = len(first)
    print(f"\n{label}  (n={n} matches)")
    print(f"  1st innings: mean {st.mean(first):5.1f}  median {st.median(first):5.1f}"
          f"  sd {st.pstdev(first):4.1f}  P10 {pctl(first,10)}  P90 {pctl(first,90)}")
    print(f"  2nd innings: mean {st.mean(second):5.1f}")
    print(f"  bat-first win rate: {100*batfirst_wins/n:4.1f}%")
    print(f"  avg wickets / innings: {st.mean(wkts):4.2f}")
    print(f"  1st-inns 200+: {100*sum(1 for s in first if s>=200)/n:4.1f}%   "
          f"under 140: {100*sum(1 for s in first if s<140)/n:4.1f}%")


# ---- REAL IPL from Cricsheet ---------------------------------------------
def real_ipl():
    first, second, batfirst_wins, wkts = [], [], 0, []
    files = glob.glob(str(ROOT / "data/cricsheet/ipl/*.json"))
    for f in files:
        try:
            d = json.load(open(f))
        except Exception:
            continue
        inns = d.get("innings", [])
        if len(inns) < 2:
            continue
        totals, balls, wk = [], [], []
        for i in inns[:2]:
            runs = w = b = 0
            for ov in i.get("overs", []):
                for dl in ov.get("deliveries", []):
                    runs += dl["runs"]["total"]
                    b += 1
                    if "wickets" in dl:
                        w += len(dl["wickets"])
            totals.append(runs); balls.append(b); wk.append(w)
        if balls[0] < 108:          # skip rain-shortened 1st innings (<18 overs)
            continue
        first.append(totals[0]); second.append(totals[1]); wkts.append(wk[0])
        outcome = d["info"].get("outcome", {})
        winner = outcome.get("winner")
        teams = d["info"].get("teams", [])
        # team batting first = the batting_team of innings[0]
        bat_first_team = inns[0].get("team")
        if winner and bat_first_team and winner == bat_first_team:
            batfirst_wins += 1
    return first, second, batfirst_wins, wkts


# ---- SIMULATOR -----------------------------------------------------------
def sim(n=600):
    players = load_players()
    teams = load_teams(players)
    first, second, batfirst_wins, wkts = [], [], 0, []
    for _ in range(n):
        a, b = random.sample(teams, 2)
        r = MatchEngine(a, b).simulate()
        i1, i2 = r.innings_1, r.innings_2
        if not i1 or not i2:
            continue
        first.append(i1.score); second.append(i2.score); wkts.append(i1.wickets)
        if r.winner and r.winner.team_id == i1.batting_team.team_id:
            batfirst_wins += 1
    return first, second, batfirst_wins, wkts


if __name__ == "__main__":
    print("=" * 66)
    print("  ENGINE VALIDATION — simulator vs real IPL (Cricsheet)")
    print("=" * 66)
    summarize("REAL IPL", *real_ipl())
    summarize("SIMULATOR", *sim())
