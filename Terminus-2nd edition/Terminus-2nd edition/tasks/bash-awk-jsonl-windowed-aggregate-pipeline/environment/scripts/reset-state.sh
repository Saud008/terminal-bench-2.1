#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
STATE="${ROOT}/state"
OUTPUT="${ROOT}/output"

mkdir -p "${STATE}" "${OUTPUT}"
rm -f \
  "${STATE}/accepted.ndjson" \
  "${STATE}/ingest-stats.json" \
  "${STATE}/bucket-rollup.ndjson" \
  "${STATE}/ledger-manifest.json" \
  "${STATE}/run-seq.json" \
  "${OUTPUT}/aggregate-report.json"
