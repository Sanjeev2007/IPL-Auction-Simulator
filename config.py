"""
Global configuration for the IPL Auction Simulation System.

All tunable parameters — file paths, rating weights, simulation settings,
and baseline probabilities — are defined here. Import this module from
anywhere in the codebase to access config values.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

# Root of the project (ipl-auction-simulator/)
PROJECT_ROOT = Path(__file__).resolve().parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
ENRICHED_DATA_DIR = DATA_DIR / "enriched"
TEAMS_DATA_DIR = DATA_DIR / "teams"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Input files
RAW_CSV_PATH = RAW_DATA_DIR / "ipl_auction_players.csv"

# Output files (Phase 1)
PLAYERS_MASTER_PATH = ENRICHED_DATA_DIR / "players_master.csv"

# Output files (Phase 2)
IPL_STATS_PATH = ENRICHED_DATA_DIR / "ipl_stats.csv"
OTHER_T20_STATS_PATH = ENRICHED_DATA_DIR / "other_t20_stats.csv"
RECENT_FORM_PATH = ENRICHED_DATA_DIR / "recent_form.csv"
NEWS_SENTIMENT_PATH = ENRICHED_DATA_DIR / "news_sentiment.csv"
DERIVED_SCORES_PATH = ENRICHED_DATA_DIR / "derived_scores.csv"

# Output files (Phase 5-6)
TEAM_ROSTERS_PATH = TEAMS_DATA_DIR / "team_rosters.json"
SIMULATION_RESULTS_PATH = OUTPUT_DIR / "simulation_results.json"
TEAM_RANKINGS_PATH = OUTPUT_DIR / "team_rankings.csv"

# ---------------------------------------------------------------------------
# Price parsing
# ---------------------------------------------------------------------------

# Multipliers for base price notation used in the CSV
PRICE_MULTIPLIERS = {
    "C": 10_000_000,    # 1 Crore = 10,000,000
    "L": 100_000,       # 1 Lakh  = 100,000
}

# ---------------------------------------------------------------------------
# Player ID prefixes by role
# ---------------------------------------------------------------------------

ROLE_ID_PREFIX = {
    "Batsmen": "BAT",
    "Wicketkeepers": "WK",
    "All Rounders": "AR",
    "Fast Bowlers": "PACE",
    "Spinners": "SPIN",
}

# ---------------------------------------------------------------------------
# Rating weights (Phase 3)
# ---------------------------------------------------------------------------

# Batting rating composition
BATTING_RATING_WEIGHTS = {
    "ipl": 0.60,
    "other_t20": 0.25,
    "recent_form": 0.15,
}

# Bowling rating composition
BOWLING_RATING_WEIGHTS = {
    "ipl": 0.60,
    "other_t20": 0.25,
    "recent_form": 0.15,
}

# Overall rating composition
OVERALL_RATING_WEIGHTS = {
    "statistical": 0.85,
    "popularity": 0.10,
    "news_context": 0.05,
}

# ---------------------------------------------------------------------------
# Simulation settings (Phase 4-5)
# ---------------------------------------------------------------------------

SIMULATION_ITERATIONS = 1000          # number of full tournament runs
BALLS_PER_INNINGS = 120               # 20 overs × 6 balls
MAX_WICKETS = 10
MAX_OVERS_PER_BOWLER = 4
POINTS_PER_WIN = 2

# Match phases (over ranges, 0-indexed)
PHASES = {
    "powerplay": (0, 6),              # overs 1-6
    "middle": (6, 16),                # overs 7-16
    "death": (16, 20),                # overs 17-20
}

# ---------------------------------------------------------------------------
# Baseline ball-outcome probabilities (Phase 3)
# ---------------------------------------------------------------------------
# These represent league-average probabilities for each outcome per phase.
# Used as the denominator in the geometric-mean blending formula.

BASELINE_PROBABILITIES = {
    "powerplay": {
        "dot": 0.35,
        "single": 0.28,
        "double": 0.08,
        "triple": 0.01,
        "four": 0.12,
        "six": 0.06,
        "wicket": 0.10,
    },
    "middle": {
        "dot": 0.38,
        "single": 0.30,
        "double": 0.08,
        "triple": 0.01,
        "four": 0.10,
        "six": 0.05,
        "wicket": 0.08,
    },
    "death": {
        "dot": 0.30,
        "single": 0.22,
        "double": 0.06,
        "triple": 0.01,
        "four": 0.14,
        "six": 0.15,
        "wicket": 0.12,
    },
}

# ---------------------------------------------------------------------------
# IPL Teams (for tournament simulation)
# ---------------------------------------------------------------------------

IPL_TEAMS = [
    ("CSK", "Chennai Super Kings"),
    ("MI", "Mumbai Indians"),
    ("RCB", "Royal Challengers Bengaluru"),
    ("KKR", "Kolkata Knight Riders"),
    ("DC", "Delhi Capitals"),
    ("PBKS", "Punjab Kings"),
    ("RR", "Rajasthan Royals"),
    ("SRH", "Sunrisers Hyderabad"),
    ("GT", "Gujarat Titans"),
    ("LSG", "Lucknow Super Giants"),
]
