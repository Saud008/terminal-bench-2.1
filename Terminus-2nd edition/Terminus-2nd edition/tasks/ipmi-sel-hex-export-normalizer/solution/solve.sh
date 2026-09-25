#!/bin/bash
set -euo pipefail

PATCH_DIR="$(cd "$(dirname "$0")/patches" && pwd)"
cd /app

cp "${PATCH_DIR}/parse.sh" lib/parse.sh
cp "${PATCH_DIR}/sensor_map.sh" lib/sensor_map.sh
cp "${PATCH_DIR}/sel-ingest.sh" scripts/sel-ingest.sh
cp "${PATCH_DIR}/sel-export.sh" scripts/sel-export.sh
chmod +x lib/*.sh scripts/*.sh

mkdir -p /app/state /app/output
rm -f /app/state/sel.db /app/state/sel.stage

/app/bin/sel-chain ingest --input /app/fixtures/sel_alpha.bin --db /app/state/sel.db
/app/bin/sel-chain export --db /app/state/sel.db --out /app/output/sel-events.csv
