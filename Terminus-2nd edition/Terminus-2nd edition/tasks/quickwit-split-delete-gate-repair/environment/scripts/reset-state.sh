#!/usr/bin/env bash
set -euo pipefail
rm -f /app/data/qwindex.db
rm -f /app/state/manifest.json /app/state/checkpoint.json /app/state/merge-audit.json
rm -f /app/state/search-report.json /app/state/delete-audit.json /app/state/split-meta.json
rm -f /app/output/search-export.json
mkdir -p /app/data /app/state /app/output
