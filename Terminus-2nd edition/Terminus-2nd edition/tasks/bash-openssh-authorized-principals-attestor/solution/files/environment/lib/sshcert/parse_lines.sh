#!/usr/bin/env bash
set -euo pipefail

SSHAP_LIB="${SSHAP_LIB:-/app/lib}"
# shellcheck source=/app/lib/common.sh
source "${SSHAP_LIB}/common.sh"

read_principal_files() {
  local dir="$1"
  local rows=()
  local f base
  for f in "$dir"/*.principals; do
    [[ -f "$f" ]] || continue
    base="$(basename "$f" .principals)"
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | xargs)"
      [[ -z "$line" ]] && continue
      local deny=0 text="$line"
      if [[ "$line" == !* ]]; then
        deny=1
        text="${line#!}"
      fi
      local rank=0
      [[ "$deny" -eq 0 ]] && rank="$(principal_specificity "$text")"
      rows+=("${base}|${deny}|${rank}|${text}")
    done < "$f"
  done
  printf '%s\n' "${rows[@]}"
}
