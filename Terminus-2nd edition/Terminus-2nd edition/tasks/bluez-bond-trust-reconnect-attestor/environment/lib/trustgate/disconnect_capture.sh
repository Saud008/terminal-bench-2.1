#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh
source /app/lib/intake/device_table.sh

set_adapter_power() {
  local state="$1"
  write_adapter_power "$state"
  append_ledger_row "{\"event\":\"adapter_power\",\"state\":\"${state}\"}"
}

record_disconnect() {
  local mac="$1" reason="$2"
  local power
  power="$(read_adapter_power)"
  python3 - "$mac" "$reason" "$power" "${DISCONNECT_JSON}" <<'PY'
import json, sys
mac, reason, power, path = sys.argv[1:5]
rows = json.load(open(path, encoding="utf-8"))
rows.append({"mac": mac, "reason": reason, "adapter_power": power})
json.dump(rows, open(path, "w", encoding="utf-8"))
PY
  append_ledger_row "{\"event\":\"disconnect\",\"mac\":\"${mac}\",\"reason\":\"${reason}\",\"adapter_power\":\"${power}\"}"
  python3 - "$(mac_to_file "$mac")" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.is_file():
    raise SystemExit
doc = json.load(open(p, encoding="utf-8"))
doc["pairing_confirmed"] = False
json.dump(doc, open(p, "w", encoding="utf-8"))
PY
}
