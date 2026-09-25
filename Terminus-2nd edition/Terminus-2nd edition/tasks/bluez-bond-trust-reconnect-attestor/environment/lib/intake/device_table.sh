#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

mac_to_file() {
  echo "${LEDGER_DIR}/$(echo "$1" | tr ':' '_').json"
}

read_device_field() {
  local mac="$1" field="$2"
  python3 - "$(mac_to_file "$mac")" "$field" <<'PY'
import json, sys
from pathlib import Path

path, field = sys.argv[1], sys.argv[2]
if not Path(path).is_file():
    print("" if field != "trusted" else "false")
    raise SystemExit
doc = json.load(open(path, encoding="utf-8"))
val = doc.get(field, "")
if isinstance(val, bool):
    print("true" if val else "false")
else:
    print(val)
PY
}

write_device_json() {
  python3 - "$(mac_to_file "$1")" "$2" <<'PY'
import json, sys
json.dump(json.loads(sys.argv[2]), open(sys.argv[1], "w", encoding="utf-8"))
PY
}

seed_bond() {
  local mac="$1" addr_type="$2" trusted="$3" token="$4"
  write_device_json "$mac" "{\"addr_type\":\"${addr_type}\",\"trusted\":${trusted},\"resume_token\":\"${token}\",\"bonded\":true,\"pairing_confirmed\":false}"
  append_ledger_row "{\"event\":\"seed_bond\",\"mac\":\"${mac}\",\"addr_type\":\"${addr_type}\",\"resume_token\":\"${token}\"}"
}
