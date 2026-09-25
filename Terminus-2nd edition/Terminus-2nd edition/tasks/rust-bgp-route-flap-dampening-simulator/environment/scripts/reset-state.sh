#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/scenario-lock.json /app/state/flap-ledger.json /app/state/run-counter.json
rm -f /app/output/suppression-atlas.jsonl /app/output/*.jsonl 2>/dev/null || true
mkdir -p /app/state /app/output
