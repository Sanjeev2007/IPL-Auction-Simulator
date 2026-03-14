#!/usr/bin/env python3
"""
Run Phase 1: Data Ingestion

Reads the raw auction CSV, normalizes it, and outputs players_master.csv.

Usage:
    python scripts/run_ingestion.py
"""

import sys
from pathlib import Path

# Ensure project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.dataset_builder import build_players_master


def main():
    print("=" * 60)
    print("  IPL Auction Simulator — Phase 1: Data Ingestion")
    print("=" * 60)
    print()

    players = build_players_master()

    print()
    print("=" * 60)
    print(f"  ✅ Phase 1 complete — {len(players)} players in dataset")
    print("=" * 60)


if __name__ == "__main__":
    main()
