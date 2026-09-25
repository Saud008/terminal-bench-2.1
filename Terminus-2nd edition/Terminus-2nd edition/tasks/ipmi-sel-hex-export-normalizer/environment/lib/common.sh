#!/usr/bin/env bash
# Shared helpers for sel-chain modules.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

die() {
  echo "sel-chain: $*" >&2
  exit 1
}

require_db() {
  local db="$1"
  [ -f "${db}" ] || die "database not found: ${db}"
}

state_dir_for() {
  local db="$1"
  dirname "${db}"
}

stage_path_for() {
  local db="$1"
  echo "$(state_dir_for "${db}")/sel.stage"
}

ensure_schema() {
  local db="$1"
  sqlite3 "${db}" < "${APP_ROOT}/lib/schema.sql"
}

read_u8() {
  local file="$1"
  local offset="$2"
  xxd -s "${offset}" -l 1 -p "${file}" | awk '{print strtonum("0x"$0)}'
}

read_u16_le() {
  local file="$1"
  local offset="$2"
  xxd -s "${offset}" -l 2 -p "${file}" | awk '{print strtonum("0x" substr($0,3,2) substr($0,1,2))}'
}

read_u32_le() {
  local file="$1"
  local offset="$2"
  xxd -s "${offset}" -l 4 -p "${file}" | awk '{print strtonum("0x" substr($0,7,2) substr($0,5,2) substr($0,3,2) substr($0,1,2))}'
}

severity_for_event_type() {
  local et="$1"
  case "${et}" in
    1|2|3) echo "critical" ;;
    6|7|8) echo "warning" ;;
    *) echo "info" ;;
  esac
}

severity_rank() {
  local label="$1"
  case "${label}" in
    critical) echo 0 ;;
    warning) echo 1 ;;
    *) echo 2 ;;
  esac
}

ts_to_iso() {
  local ts="$1"
  date -u -d "@${ts}" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -r "${ts}" '+%Y-%m-%dT%H:%M:%SZ'
}
