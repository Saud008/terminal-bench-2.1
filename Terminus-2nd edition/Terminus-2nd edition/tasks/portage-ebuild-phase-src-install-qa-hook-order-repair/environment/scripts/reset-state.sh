#!/usr/bin/env bash
set -euo pipefail

rm -rf /app/state/* /app/output/* /app/work/* 2>/dev/null || true
mkdir -p /app/state /app/output /app/work
printf '{"steps":[]}\n' > /app/state/phase-trace.json
printf '{"records":[]}\n' > /app/state/merge-ledger.json
