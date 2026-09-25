#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

rm -f /app/work/ledger.db
rm -f /app/state/replay-snapshot.json
rm -f /app/state/replay-generation.json
rm -rf /app/output/*
mkdir -p /app/work /app/state /app/output

unset TB3_CLOCK_START TB3_TICK_MS TB3_FIXTURE_DIR TB3_TZ
