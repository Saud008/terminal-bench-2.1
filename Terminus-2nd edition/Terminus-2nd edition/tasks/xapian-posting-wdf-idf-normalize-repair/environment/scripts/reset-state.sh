#!/usr/bin/env bash
set -euo pipefail
mkdir -p /app/work /app/output /app/state
echo '{"documents":[],"next_order":0}' > /app/work/index.json
rm -f /app/state/index-staging.json /app/output/*.json 2>/dev/null || true
