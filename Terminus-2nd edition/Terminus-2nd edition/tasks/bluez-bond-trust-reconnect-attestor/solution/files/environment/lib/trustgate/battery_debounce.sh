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
  local path="$1"
  if [[ -f "$path" ]]; then
    tr -d '[:space:]' < "$path"
  else
    printf '%s' '-10000'
  fi
}

_should_suppress_reconnect() {
  local mac="$1" ts="$2"
  local debounce_ms last_file last
  debounce_ms="$(_debounce_window_ms)"
  last_file="$(_last_reconnect_path "$mac")"
  last="$(_read_last_reconnect_ts "$last_file")"
  if (( ts - last < debounce_ms )); then
    return 0
  fi
  return 1
}

_record_reconnect_ts() {
  local mac="$1" ts="$2"
  local last_file
  last_file="$(_last_reconnect_path "$mac")"
  mkdir -p "$(dirname "$last_file")"
  printf '%s\n' "$ts" > "$last_file"
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
