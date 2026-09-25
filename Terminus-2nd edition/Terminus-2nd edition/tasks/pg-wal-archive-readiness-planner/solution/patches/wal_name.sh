#!/usr/bin/env bash
# Parse PostgreSQL WAL segment filenames (24 hex chars).
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
# shellcheck source=common.sh
source "${APP_ROOT}/lib/common.sh"

split_wal_name() {
  local name="$1"
  local base="${name%.partial}"
  if [[ ! "${base}" =~ ^[0-9A-Fa-f]{24}$ ]]; then
    return 1
  fi
  local timeline=$((16#${base:0:8}))
  local segment=$((16#${base:8:16}))
  echo "${timeline} ${segment}"
}

wal_segment_hex() {
  local timeline="$1"
  local segment="$2"
  printf "%08X%016X" "${timeline}" "${segment}"
}
