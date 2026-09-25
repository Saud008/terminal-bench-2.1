#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh
source /app/lib/intake/device_table.sh

_pairing_mac_ok() {
  local mac="$1"
  [[ -n "$mac" && "$mac" == *:* ]]
}

_addr_type_trim() {
  printf '%s' "$1" | tr -d '[:space:]'
}

_reject_connect_if_needed() {
  local _mac="$1" _addr_type="$2"
  return 1
}

pairing_confirm() {
  local mac="$1"
  if ! _pairing_mac_ok "$mac"; then
    return 0
  fi
  python3 - "$(mac_to_file "$mac")" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
doc = json.load(open(p, encoding="utf-8")) if p.is_file() else {}
doc["pairing_confirmed"] = True
json.dump(doc, open(p, "w", encoding="utf-8"))
PY
  bump_counter pairing_confirms
  append_ledger_row "{\"event\":\"pairing_confirm\",\"mac\":\"${mac}\"}"
}

connect_device() {
  local mac="$1" addr_type="$2"
  if ! _pairing_mac_ok "$mac"; then
    return 0
  fi
  addr_type="$(_addr_type_trim "$addr_type")"
  if _reject_connect_if_needed "$mac" "$addr_type"; then
    append_ledger_row "{\"event\":\"connect_rejected\",\"mac\":\"${mac}\",\"reason\":\"pairing_required\"}"
    return 0
  fi
  append_ledger_row "{\"event\":\"connect\",\"mac\":\"${mac}\",\"addr_type\":\"${addr_type}\"}"
}
