"""
Player Name Matcher — Maps Cricsheet abbreviated names to players_master Player_IDs.

Cricsheet uses abbreviated names like "V Kohli", "JJ Bumrah", "AB de Villiers".
Our players_master has full names like "Virat Kohli", "Boom Boom", "SKY".

This module builds a fuzzy matching system:
  1. Exact surname match + first-initial match (most reliable)
  2. Known alias mapping for nicknames/abbreviations
  3. Fuzzy fallback for remaining matches
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Known aliases: maps our CSV name → possible Cricsheet names
# ---------------------------------------------------------------------------

KNOWN_ALIASES = {
    # Nicknames / abbreviations in our CSV
    "Sky": ["SPD Yadav", "SA Yadav", "Suryakumar Yadav"],
    "Msd": ["MS Dhoni"],
    "Kl Rahul": ["KL Rahul"],
    "Qdk": ["Q de Kock"],
    "Boom Boom": ["JJ Bumrah"],
    "Ak47": ["Ankit Rajpoot"],  # or could be another player
    "Nkr": ["Nitish Kumar Reddy", "N Kumar Reddy"],
    "Washy Sundar": ["W Sundar", "Washington Sundar"],
    "Yuzi Chahal": ["YS Chahal"],
    "Faf Du Plessis": ["F du Plessis"],
    "Eshan Malinga": ["E Malinga"],

    # Players whose Cricsheet names differ significantly
    "Markram": ["AK Markram"],
    "Natarajan": ["T Natarajan"],
    "Rovman Powell": ["R Powell"],
    "Shimron Hetmyer": ["SO Hetmyer"],
    "Rachin Ravindra": ["R Ravindra"],
    "Venky Iyer": ["V Iyer"],
    "Sikandhar Raza": ["Sikandar Raza"],
    "Shakib Al-Hasan": ["Shakib Al Hasan"],
    "Naveen-Ul-Haq": ["Naveen-ul-Haq"],
    "Mujeeb-Ur-Rahman": ["Mujeeb Ur Rahman"],
    "Rahmanullah Gurbaz": ["Rahmanullah Gurbaz"],
    "Allah Ghazanfar": ["Allah Ghazanfar"],
    "M. Siddharth": ["M Siddharth"],
}


def _normalize(name: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    return re.sub(r"\s+", " ", name.strip().lower())


def _extract_surname(name: str) -> str:
    """Extract likely surname (last space-separated token)."""
    parts = name.strip().split()
    return parts[-1].lower() if parts else ""


def _extract_initial(name: str) -> str:
    """Extract first initial from Cricsheet-style name 'V Kohli' → 'v'."""
    parts = name.strip().split()
    if parts and len(parts[0]) <= 3:  # Initials like "V", "JJ", "AB"
        return parts[0][0].lower()
    return parts[0][0].lower() if parts else ""


class PlayerNameMatcher:
    """
    Matches Cricsheet player names to players_master Player_IDs.

    Build with load_master(), then call match() with Cricsheet names.
    """

    def __init__(self):
        self.players: dict[str, dict] = {}        # Player_ID → master row
        self.surname_index: dict[str, list] = defaultdict(list)  # surname → [Player_IDs]
        self.alias_map: dict[str, str] = {}        # normalized alias → Player_ID
        self._cache: dict[str, str | None] = {}    # cricsheet_name → Player_ID (cached)

    def load_master(self, master_path: Path) -> None:
        """Load players_master.csv and build lookup indices."""
        with open(master_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pid = row["Player_ID"]
                name = row["Player Name"]
                self.players[pid] = row

                # Index by surname
                surname = _extract_surname(name)
                self.surname_index[surname].append(pid)

                # Add known aliases
                if name in KNOWN_ALIASES:
                    for alias in KNOWN_ALIASES[name]:
                        self.alias_map[_normalize(alias)] = pid

                # Also add the full name as-is (normalized)
                self.alias_map[_normalize(name)] = pid

        print(f"   📇 Loaded {len(self.players)} players, "
              f"{len(self.alias_map)} aliases, "
              f"{len(self.surname_index)} unique surnames")

    def match(self, cricsheet_name: str) -> str | None:
        """
        Find the Player_ID for a Cricsheet player name.

        Returns Player_ID or None if no match found.
        """
        if cricsheet_name in self._cache:
            return self._cache[cricsheet_name]

        pid = self._do_match(cricsheet_name)
        self._cache[cricsheet_name] = pid
        return pid

    def _do_match(self, name: str) -> str | None:
        norm = _normalize(name)

        # 1. Direct alias match
        if norm in self.alias_map:
            return self.alias_map[norm]

        # 2. Surname + initial match
        surname = _extract_surname(name)
        candidates = self.surname_index.get(surname, [])

        if len(candidates) == 1:
            # Unique surname match
            return candidates[0]

        if len(candidates) > 1:
            # Multiple players with same surname — use initial
            initial = _extract_initial(name)
            for pid in candidates:
                pname = self.players[pid]["Player Name"]
                if pname[0].lower() == initial:
                    return pid
            # If no initial match, return first candidate (best guess)
            return candidates[0]

        # 3. Partial surname match (handles "du Plessis" vs "Plessis")
        for sn, pids in self.surname_index.items():
            if sn in norm or norm.endswith(sn):
                if len(pids) == 1:
                    return pids[0]

        return None

    def get_match_stats(self) -> dict:
        """Return stats about matching performance."""
        total = len(self._cache)
        matched = sum(1 for v in self._cache.values() if v is not None)
        return {
            "total_unique_names": total,
            "matched": matched,
            "unmatched": total - matched,
            "match_rate": round(matched / total * 100, 1) if total else 0,
        }
