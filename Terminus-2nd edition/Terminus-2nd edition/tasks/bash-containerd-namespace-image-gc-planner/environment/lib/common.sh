#!/usr/bin/env bash
set -euo pipefail

CTGC_LIB="${CTGC_LIB:-/app/lib}"

sha256_lines() {
  printf '%s' "$1" | sha256sum | awk '{print $1}'
}

ensure_state_dir() {
  mkdir -p /app/state /app/output
}

read_revision_seq() {
  local f="/app/state/revision.seq"
  if [[ -f "$f" ]]; then
    tr -d '[:space:]' < "$f"
  else
    echo 0
  fi
}

write_revision_seq() {
  local val="$1"
  ensure_state_dir
  printf '%s\n' "$val" > /app/state/revision.seq
}

digest_file_json() {
  local path="$1"
  jq -c -S '.' "$path" | sha256sum | awk '{print $1}'
}
