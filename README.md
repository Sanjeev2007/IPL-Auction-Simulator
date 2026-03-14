# IPL Auction Simulator

A probabilistic IPL match and tournament simulation system built from auction player data.

## Project Structure

```
ipl-auction-simulator/
├── config.py               # Global configuration
├── data/
│   ├── raw/                # Input data (CSV, images)
│   ├── enriched/           # Processed datasets
│   └── teams/              # Team rosters
├── src/
│   ├── models/             # Data models (Player, Team, Match, Tournament)
│   ├── ingestion/          # CSV parsing, OCR extraction
│   ├── enrichment/         # Stats fetchers, news analysis
│   ├── rating/             # Rating model, probability mapper
│   ├── simulation/         # Match & tournament engines
│   └── analytics/          # Aggregation, visualization
├── scripts/                # CLI runner scripts
├── tests/                  # Unit tests
└── output/                 # Simulation results
```

## Quick Start

```bash
# Phase 1: Build players_master dataset
python scripts/run_ingestion.py
```

## Development Phases

1. ✅ **Data Foundation** — Models, config, dataset builder
2. ⬜ **Enrichment** — IPL stats, T20 stats, recent form, news
3. ⬜ **Rating Engine** — Weighted ratings, probability mapping
4. ⬜ **Match Simulation** — Ball-by-ball T20 match engine
5. ⬜ **Tournament** — Full season + playoffs simulation
6. ⬜ **Analytics** — Aggregation, rankings, visualization
