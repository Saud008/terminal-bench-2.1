#!/usr/bin/env bash
set -euo pipefail

rm -f /app/work/livattest.db
rm -f /app/output/attest-report.json
rm -f /app/state/witness-snapshot.json
mkdir -p /app/work /app/output /app/state
