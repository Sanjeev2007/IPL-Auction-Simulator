#!/usr/bin/env bash
#
# Downloads the raw Cricsheet ball-by-ball data this project derives ratings from.
#
# You do NOT need this to run the app or the simulator — the enriched rating CSVs
# (data/enriched/*.csv) and team lineups are committed. You only need this to
# RE-RUN enrichment from scratch (scripts/run_real_enrichment.py). ~450 MB unzipped.
#
# Source: https://cricsheet.org (freely licensed under the Odds & Sods terms).
#
set -euo pipefail

BASE="https://cricsheet.org/downloads"
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/data/cricsheet"

# local_folder : remote_zip  (the T20I feed is published as t20s_json.zip)
SETS=(
  "ipl:ipl_json.zip"
  "t20i:t20s_json.zip"
  "bbl:bbl_json.zip"
  "cpl:cpl_json.zip"
  "psl:psl_json.zip"
)

command -v unzip >/dev/null 2>&1 || { echo "error: 'unzip' is required" >&2; exit 1; }
mkdir -p "$DEST"

for entry in "${SETS[@]}"; do
  folder="${entry%%:*}"
  zip="${entry##*:}"
  echo "→ $zip  →  data/cricsheet/$folder/"
  tmp="$(mktemp)"
  curl -fSL "$BASE/$zip" -o "$tmp"
  mkdir -p "$DEST/$folder"
  unzip -oq "$tmp" -d "$DEST/$folder"
  rm -f "$tmp"
done

echo "✓ Cricsheet data downloaded to data/cricsheet/"
echo "  Regenerate ratings with:  python scripts/run_real_enrichment.py"
