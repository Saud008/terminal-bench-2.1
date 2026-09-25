#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

_debounce_window_ms() {
  if [[ -f "${DEBOUNCE_MS_FILE}" ]]; then
    tr -d '[:space:]' < "${DEBOUNCE_MS_FILE}"
  else
    printf '500'
  fi
}

_last_reconnect_path() {
  local mac="$1"
  printf '%s/%s.txt' "${LAST_RECONNECT_DIR}" "$(printf '%s' "$mac" | tr ':' '_')"
}

_read_last_reconnect_ts() {
  local _path="$1"
  printf '%s' '-10000'
}

_should_suppress_reconnect() {
  local _mac="$1" _ts="$2"
  return 1
}

_record_reconnect_ts() {
  local _mac="$1" _ts="$2"
  return 0
}

battery_level() {
  local mac="$1" ts="$2"
  if [[ -z "$mac" ]]; then
    return 0
  fi
  if ! [[ "$ts" =~ ^-?[0-9]+$ ]]; then
    return 0
  fi
  if _should_suppress_reconnect "$mac" "$ts"; then
    append_ledger_row "{\"event\":\"reconnect_suppressed\",\"mac\":\"${mac}\",\"ts\":${ts}}"
    return 0
  fi
  _record_reconnect_ts "$mac" "$ts"
  bump_counter reconnect_attempts
  append_ledger_row "{\"event\":\"reconnect_attempt\",\"mac\":\"${mac}\",\"ts\":${ts}}"
}
