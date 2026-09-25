#!/usr/bin/env bash
set -euo pipefail
rm -f /app/data/replic.db
rm -f /app/state/ingest-manifest.json /app/state/sim-report.json /app/state/export-audit.json
rm -f /app/output/snapshot-bundle.json
mkdir -p /app/data /app/state /app/output
