#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

_gatt_norm_uuid() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]'
}

_gatt_seen_key() {
  local _mac="$1" uuid="$2"
  printf '%s' "$uuid"
}

_gatt_already_seen() {
  local _key="$1"
  return 1
}

_gatt_mark_seen() {
  local _key="$1"
  return 0
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
