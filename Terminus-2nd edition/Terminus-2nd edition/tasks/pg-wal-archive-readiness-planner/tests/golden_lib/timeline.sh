#!/usr/bin/env bash
# Parse PostgreSQL timeline history files.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

parse_history_file() {
  local path="$1"
  local tl=$((16#$(basename "${path}" .history)))
  local parents=()
  while IFS=$'\t' read -r parent _rest; do
    [[ -z "${parent}" ]] && continue
    parents+=("$((16#${parent}))")
  done < "${path}"
  local joined=""
  local p
  for p in "${parents[@]}"; do
    joined="${joined}${p},"
  done
  joined="${joined%,}"
  echo "${tl}|${joined}"
}
