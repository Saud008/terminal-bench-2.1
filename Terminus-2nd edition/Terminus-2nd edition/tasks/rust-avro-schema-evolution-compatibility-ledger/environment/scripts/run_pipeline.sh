#!/usr/bin/env bash
set -euo pipefail
/app/environment/scripts/build_all.sh
mkdir -p /app/state /app/output
SCHEMA_DIR="${TB3_SCHEMA_DIR:-/app/environment/fixtures/schemas}"
PAIRS="${TB3_PAIRS_FILE:-/app/environment/fixtures/schema_pairs.jsonl}"
/app/environment/tools/avsccompat/avsccompat ingest \
  --schema-dir "$SCHEMA_DIR" \
  --pairs "$PAIRS" \
  --staging /app/state/schema_pair_ledger.jsonl
/app/environment/tools/avsccompat/avsccompat export \
  --staging /app/state/schema_pair_ledger.jsonl \
  --out /app/output/avro_migration_report.json
