#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p1 -d /app < patches/parse__load_map.sh.patch
patch -p1 -d /app < patches/osd__filter_status.sh.patch
patch -p1 -d /app < patches/bucket__traverse.sh.patch
patch -p1 -d /app < patches/weight__normalize.sh.patch
patch -p1 -d /app < patches/rule__apply_steps.sh.patch
patch -p1 -d /app < patches/trace__trace_pg.sh.patch
patch -p1 -d /app < patches/workspace__normalized_fingerprint.sh.patch
patch -p1 -d /app < patches/export__export_ledger.sh.patch
bash /app/scripts/rebuild-crpe.sh
bash /app/scripts/reset-state.sh
/app/bin/crpe ingest --map coastal-pool --run-id oracle-smoke >/dev/null
/app/bin/crpe normalize --run-id oracle-smoke >/dev/null
test -s /app/state/crpe-normalized.json
/app/bin/crpe export-ledger --run-id oracle-smoke --pg-start 0 --pg-end 3 --output /app/output/oracle-smoke-ledger.json >/dev/null
test -s /app/output/oracle-smoke-ledger.json
