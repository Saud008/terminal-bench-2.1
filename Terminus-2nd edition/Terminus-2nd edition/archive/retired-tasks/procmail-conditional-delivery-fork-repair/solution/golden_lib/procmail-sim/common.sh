#!/usr/bin/env bash
# Shared paths and helpers for the procmail-sim modules.
ROOT="/app"
STATE_DIR="${ROOT}/state"
LOCK_ROOT="${STATE_DIR}/locks"
SNAPSHOT_DEFAULT="${STATE_DIR}/delivery-snapshot.json"

pm_trim() {
  local s=""
  if [[ $# -ge 1 ]]; then
    s="$1"
  else
    IFS= read -r s || s=""
  fi
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

pm_headers_only() {
  local body=""
  if [[ $# -ge 1 ]]; then
    body="$1"
  else
    IFS= read -r body || body=""
  fi
  awk 'BEGIN{n=1} {if(n && $0==""){n=0; next} if(n) print}' <<<"$body"
}
