#!/bin/bash
set -euo pipefail

DB="/app/data/metrics.db"
SCHEMA="/app/data/schema.sql"

rm -f "$DB"
sqlite3 "$DB" < "$SCHEMA"
mkdir -p /app/output /app/state /app/work
rm -f /app/output/query-report.json /app/state/scrape-manifest.json /app/state/rollup-snapshot.json /app/state/cache-index.json
