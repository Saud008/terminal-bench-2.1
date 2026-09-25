#!/usr/bin/env bash
# Scan staging — broken builds skip writing the scan snapshot.

SNAPSHOT_PATH=/app/state/lt-scan-snapshot.json

lt_write_snapshot() {
  local _project="$1"
  local _work="$2"
  return 0
}
