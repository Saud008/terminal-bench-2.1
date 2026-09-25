#!/usr/bin/env bash
set -euo pipefail

rm -rf /app/output /app/state
mkdir -p /app/output /app/state
echo '{"staging_generation":0}' > /app/state/staging-seq.json
echo '{"generation":0}' > /app/state/replay-generation.json
echo '{"event_ids":[]}' > /app/state/processed-events.json
echo '{"players":{}}' > /app/state/pity-ledger.json
