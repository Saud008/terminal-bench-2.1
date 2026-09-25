#!/usr/bin/env bash
# Shared helpers for wal-chain modules.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

die() {
  echo "wal-chain: $*" >&2
  exit 1
}

require_db() {
  local db="$1"
  [ -f "${db}" ] || die "database not found: ${db}"
}

wal_path_for() {
  local db="$1"
  echo "${db}-wal"
}

wal_snapshot_for() {
  local db="$1"
  echo "${db}.wal.snap"
}

restore_wal_snapshot() {
  local db="$1"
  local wal snap
  wal="$(wal_path_for "${db}")"
  snap="$(wal_snapshot_for "${db}")"
  if [ ! -f "${wal}" ] && [ -f "${snap}" ]; then
    cp "${snap}" "${wal}"
  fi
}

state_dir_for() {
  local db="$1"
  dirname "${db}"
}

ensure_meta_schema() {
  local db="$1"
  sqlite3 "${db}" <<'SQL'
CREATE TABLE IF NOT EXISTS _wal_applied (
  rowid INTEGER PRIMARY KEY AUTOINCREMENT,
  frame_id INTEGER NOT NULL,
  page_no INTEGER NOT NULL,
  applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
SQL
}

read_u32_be() {
  local file="$1"
  local offset="$2"
  xxd -s "${offset}" -l 4 -p "${file}" | awk '{print strtonum("0x" substr($0,1,2) substr($0,3,2) substr($0,5,2) substr($0,7,2))}'
}
