#!/usr/bin/env bash
# Frame iteration and bookkeeping helpers.
set -euo pipefail

frame_page_no() {
  local wal="$1"
  local frame_idx="$2"
  local psz="$3"
  local base=$((32 + (frame_idx - 1) * (24 + psz)))
  read_u32_be "${wal}" "${base}"
}

apply_frame_record() {
  local db="$1"
  local frame_id="$2"
  local page_no="$3"
  sqlite3 "${db}" "INSERT INTO _wal_applied (frame_id, page_no) VALUES (${frame_id}, ${page_no});"
}

frame_already_applied() {
  local db="$1"
  local frame_id="$2"
  local cnt
  cnt="$(sqlite3 "${db}" "SELECT COUNT(*) FROM _wal_applied WHERE frame_id=${frame_id};")"
  [ "${cnt}" -gt 0 ]
}
