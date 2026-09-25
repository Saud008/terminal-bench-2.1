#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

_gatt_norm_uuid() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]'
}

_gatt_seen_key() {
  local mac="$1" uuid="$2"
  printf '%s|%s' "$mac" "$uuid"
}

_gatt_already_seen() {
  local key="$1"
  [[ -n "$key" ]] || return 1
  grep -Fxq "$key" "${GATT_SEEN}" 2>/dev/null
}

_gatt_mark_seen() {
  local key="$1"
  [[ -n "$key" ]] || return 0
  mkdir -p "$(dirname "${GATT_SEEN}")"
  echo "$key" >> "${GATT_SEEN}"
}

gatt_discover() {
  local mac="$1" uuid="$2"
  if [[ -z "$mac" || -z "$uuid" ]]; then
    return 0
  fi
  uuid="$(_gatt_norm_uuid "$uuid")"
  local key
  key="$(_gatt_seen_key "$mac" "$uuid")"
  if _gatt_already_seen "$key"; then
    return 0
  fi
  _gatt_mark_seen "$key"
  bump_counter gatt_resolve_count
  append_ledger_row "{\"event\":\"gatt_discover\",\"mac\":\"${mac}\",\"uuid\":\"${uuid}\"}"
}
