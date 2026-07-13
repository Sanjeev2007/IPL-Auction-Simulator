"""Derived ratings must stay on the documented 0-100 scale."""
import csv
import pathlib

RATED_COLUMNS = [
    "bat_rating", "bowl_rating", "overall_rating",
    "powerplay_rating", "middle_rating", "death_rating",
    "vs_pace_rating", "vs_spin_rating",
]
CSV_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "enriched" / "derived_scores.csv"


def test_ratings_within_bounds():
    rows = list(csv.DictReader(CSV_PATH.open()))
    assert len(rows) > 200, "expected the full player pool"

    for row in rows:
        for col in RATED_COLUMNS:
            value = float(row[col])
            assert 0.0 <= value <= 100.0, f"{row['Player_ID']} {col}={value} out of 0-100"
