#!/usr/bin/env bash
# WAL sidecar ingest helpers — restore snap before reconcile reads frames.
set -euo pipefail

source /app/lib/common.sh

wal_ingest_restore_snap() {
  local db="$1"
  restore_wal_snapshot "${db}"
}
