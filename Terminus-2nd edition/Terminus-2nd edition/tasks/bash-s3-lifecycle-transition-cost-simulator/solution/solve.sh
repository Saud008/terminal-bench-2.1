#!/usr/bin/env bash
# Oracle solve — task identity bash-s3-lifecycle-transition-cost-simulator token ce63881d
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p0 -d /app < files/patches/m01.patch
patch -p0 -d /app < files/patches/m02.patch
patch -p0 -d /app < files/patches/m03.patch
patch -p0 -d /app < files/patches/m04.patch
patch -p0 -d /app < files/patches/m05.patch
patch -p0 -d /app < files/patches/m06.patch
cd /app
make install-s3lc
bash /app/scripts/reset-state.sh
CFG=/app/config/s3lc.json
INV=$(jq -r '.inventory' "$CFG")
RULES=$(jq -r '.rules' "$CFG")
HOLDS=$(jq -r '.holds' "$CFG")
RATES=$(jq -r '.rates' "$CFG")
STG=$(jq -r '.staging' "$CFG")
OUT=$(jq -r '.report_out' "$CFG")
WS=$(jq -r '.window_start' "$CFG")
WE=$(jq -r '.window_end' "$CFG")
BUCKET=$(jq -r '.bucket' "$CFG")
/usr/local/bin/s3lc ingest --inventory "$INV" --bucket "$BUCKET" --staging "$STG"
/usr/local/bin/s3lc simulate --staging "$STG" --rules "$RULES" --holds "$HOLDS" --window-start "$WS" --window-end "$WE"
/usr/local/bin/s3lc cost-report --staging "$STG" --rates "$RATES" --out "$OUT"
