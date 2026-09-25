#!/usr/bin/env bash
set -euo pipefail

STATE="/app/state"
FIXTURE_SEED="/app/fixtures/seed"
mkdir -p "${STATE}" /app/output /app/runs "${FIXTURE_SEED}"

rm -f "${STATE}/facts.db" "${STATE}/facts.staging.json"
python3 /app/tools/build_seed.py "${FIXTURE_SEED}"
