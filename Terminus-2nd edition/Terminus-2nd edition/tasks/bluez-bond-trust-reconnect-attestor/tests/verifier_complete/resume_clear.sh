#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh
source /app/lib/intake/device_table.sh

_resume_token_present() {
  local mac="$1"
  local token
  token="$(read_device_field "$mac" resume_token)"
  [[ -n "$token" ]]
}

_bond_wipe_payload() {
  local device_file="$1"
  python3 - "$device_file" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
doc = json.load(open(p, encoding="utf-8")) if p.is_file() else {}
doc.update({"bonded": False, "trusted": False, "pairing_confirmed": False, "resume_token": ""})
json.dump(doc, sys.stdout)
PY
}

bond_remove_ledger() {
  local mac="$1"
  if ! _pairing_mac_guard "$mac"; then
    return 0
  fi
  if _resume_token_present "$mac"; then
    bump_counter resume_tokens_cleared
  fi
  write_device_json "$mac" "$(_bond_wipe_payload "$(mac_to_file "$mac")")"
  append_ledger_row "{\"event\":\"bond_remove\",\"mac\":\"${mac}\"}"
}

_pairing_mac_guard() {
  local mac="$1"
  [[ -n "$mac" ]]
}
