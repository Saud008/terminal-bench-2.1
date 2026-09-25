#!/usr/bin/env bash
set -euo pipefail

STATE="/app/state"
FIXTURE_SEED="/app/fixtures/seed"
mkdir -p "${STATE}" /app/output "${FIXTURE_SEED}"

rm -f "${STATE}/ledger.db" "${STATE}/ledger.db-wal" "${STATE}/ledger.db-shm" "${STATE}/wal.stage"
rm -f "${FIXTURE_SEED}/ledger.db" "${FIXTURE_SEED}/ledger.db-wal" "${FIXTURE_SEED}/ledger.db-shm"

python3 /app/tools/build_seed_wal.py "${STATE}/ledger.db" "${FIXTURE_SEED}"
