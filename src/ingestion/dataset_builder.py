"""
Dataset Builder — Phase 1 of the IPL Auction Simulation System.

Reads the raw CSV of auction players, normalizes names, parses base prices,
assigns unique Player_IDs, validates roles, detects duplicates, and outputs
a clean players_master.csv.

Usage:
    python -m src.ingestion.dataset_builder
    # or
    python scripts/run_ingestion.py
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

# Add project root to path so we can import config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.player import Player, Role


# ---------------------------------------------------------------------------
# Price parsing
# ---------------------------------------------------------------------------

def parse_price(raw: str) -> int:
    """
    Convert a human-readable price string to integer INR value.

    Examples:
        "2C"   → 20,000,000
        "1.5C" → 15,000,000
        "50L"  → 5,000,000
        "1C"   → 10,000,000

    Args:
        raw: Price string like "2C", "50L", "1.5C"

    Returns:
        Integer value in INR

    Raises:
        ValueError: If the price string cannot be parsed
    """
    raw = raw.strip().upper()

    # Try each known suffix
    for suffix, multiplier in config.PRICE_MULTIPLIERS.items():
        if raw.endswith(suffix):
            numeric_part = raw[: -len(suffix)]
            try:
                return int(float(numeric_part) * multiplier)
            except ValueError:
                raise ValueError(f"Cannot parse numeric part of price: '{raw}'")

    # Try parsing as a plain number
    try:
        return int(raw)
    except ValueError:
        raise ValueError(
            f"Unknown price format: '{raw}'. "
            f"Expected formats: 2C, 1.5C, 50L, etc."
        )


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------

def normalize_name(name: str) -> str:
    """
    Normalize a player name:
      - Strip leading/trailing whitespace
      - Collapse multiple spaces
      - Title-case each word
      - Handle special characters (hyphens, apostrophes, dots)

    Examples:
        "  virat   KOHLI " → "Virat Kohli"
        "de villiers"      → "De Villiers"
        "naveen-ul-haq"    → "Naveen-Ul-Haq"
    """
    name = name.strip()
    name = re.sub(r"\s+", " ", name)  # collapse whitespace

    # Title-case but preserve intentional internal caps and hyphens
    parts = name.split(" ")
    normalized_parts = []
    for part in parts:
        if "-" in part:
            # Handle hyphenated names: capitalize each segment
            sub = "-".join(seg.capitalize() for seg in part.split("-"))
            normalized_parts.append(sub)
        elif "." in part:
            # Handle initials like "M." — keep as-is but ensure uppercase
            normalized_parts.append(part.upper() if len(part) <= 2 else part.title())
        else:
            normalized_parts.append(part.capitalize() if part.islower() or part.isupper() else part)
    return " ".join(normalized_parts)


# ---------------------------------------------------------------------------
# Role validation
# ---------------------------------------------------------------------------

VALID_ROLES = {"Batsmen", "Wicketkeepers", "All Rounders", "Fast Bowlers", "Spinners"}


def validate_role(role: str) -> str:
    """
    Validate and normalize a role string.

    Returns the canonical role string, or raises ValueError.
    """
    role = role.strip()

    # Direct match
    if role in VALID_ROLES:
        return role

    # Case-insensitive match
    role_lower = role.lower()
    for valid in VALID_ROLES:
        if valid.lower() == role_lower:
            return valid

    raise ValueError(
        f"Invalid role: '{role}'. "
        f"Must be one of: {', '.join(sorted(VALID_ROLES))}"
    )


# ---------------------------------------------------------------------------
# Player ID generation
# ---------------------------------------------------------------------------

def generate_player_id(role: str, counter: dict[str, int]) -> str:
    """
    Generate a unique Player_ID using the role prefix and a sequence number.

    Examples:
        "Batsmen"      → "BAT001", "BAT002", ...
        "Fast Bowlers"  → "PACE001", "PACE002", ...
    """
    prefix = config.ROLE_ID_PREFIX.get(role, "UNK")
    counter[prefix] = counter.get(prefix, 0) + 1
    return f"{prefix}{counter[prefix]:03d}"


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def detect_duplicates(names: list[str]) -> list[str]:
    """
    Find duplicate player names in the list.

    Returns list of names that appear more than once.
    """
    counts = Counter(names)
    return [name for name, count in counts.items() if count > 1]


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_players_master(
    input_path: Path = config.RAW_CSV_PATH,
    output_path: Path = config.PLAYERS_MASTER_PATH,
) -> list[Player]:
    """
    Main pipeline: read raw CSV → normalize → validate → deduplicate → output.

    Args:
        input_path:  Path to the raw CSV (ipl_auction_players.csv)
        output_path: Path for the clean output (players_master.csv)

    Returns:
        List of Player objects
    """
    print(f"📂 Reading raw CSV: {input_path}")

    # ── Step 1: Read and parse CSV ────────────────────────────────────────
    raw_rows = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip comment lines (lines starting with #)
            name = row.get("Player Name", "").strip()
            if not name or name.startswith("#"):
                continue
            raw_rows.append(row)

    print(f"   → Found {len(raw_rows)} player entries")

    # ── Step 2: Normalize and validate ────────────────────────────────────
    id_counter: dict[str, int] = {}
    players: list[Player] = []
    errors: list[str] = []

    for i, row in enumerate(raw_rows, start=1):
        try:
            name = normalize_name(row["Player Name"])
            role_str = validate_role(row["Role"])
            price = parse_price(row["Base Price"])
            player_id = generate_player_id(role_str, id_counter)

            player = Player(
                player_id=player_id,
                name=name,
                role=Role.from_csv(role_str),
                base_price=price,
            )
            players.append(player)
        except (ValueError, KeyError) as e:
            errors.append(f"   ⚠ Row {i}: {e}")

    if errors:
        print(f"\n⚠ {len(errors)} parsing errors:")
        for err in errors:
            print(err)

    # ── Step 3: Detect duplicates ─────────────────────────────────────────
    names = [p.name for p in players]
    dupes = detect_duplicates(names)
    if dupes:
        print(f"\n⚠ Duplicate names detected: {dupes}")
        print("   Keeping all entries (may need manual review)")
    else:
        print("   ✓ No duplicate names found")

    # ── Step 4: Summary by role ───────────────────────────────────────────
    role_counts = Counter(p.role.value for p in players)
    print(f"\n📊 Players by role:")
    for role, count in sorted(role_counts.items()):
        print(f"   {role:20s}: {count}")
    print(f"   {'TOTAL':20s}: {len(players)}")

    # ── Step 5: Write output CSV ──────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "Player_ID", "Player Name", "Role", "Base Price (INR)",
        "Base Price Display", "Country", "Batting Style", "Bowling Style",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in players:
            writer.writerow({
                "Player_ID": p.player_id,
                "Player Name": p.name,
                "Role": p.role.value,
                "Base Price (INR)": p.base_price,
                "Base Price Display": p.base_price_display(),
                "Country": p.country,
                "Batting Style": p.batting_style.value,
                "Bowling Style": p.bowling_style.value,
            })

    print(f"\n✅ Wrote {len(players)} players to: {output_path}")
    return players


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    players = build_players_master()
    print(f"\n🏏 Done! {len(players)} players processed.")

    # Show first 5 as a preview
    print("\n── Preview (first 5 players) ────────────────────────────")
    for p in players[:5]:
        print(f"   {p}")
