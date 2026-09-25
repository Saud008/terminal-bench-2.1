#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output/*
rm -f /app/state/repair-snapshot.json /app/state/repair-ledger.json
mkdir -p /app/output /app/state
echo "geojson-fix state reset"
