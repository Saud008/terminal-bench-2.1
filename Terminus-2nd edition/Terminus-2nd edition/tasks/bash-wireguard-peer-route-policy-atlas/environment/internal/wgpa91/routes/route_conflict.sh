#!/usr/bin/env bash
set -euo pipefail

detect_route_conflicts() {
  local routes_json="$1"
  python3 - <<'PY' "$routes_json"
import json, sys
routes = json.loads(sys.argv[1])

seen = {}
conflicts = []
for block in routes:
    iface = block.get("interface", "")
    tid = block.get("table_id")
    key = f"{iface}:{tid}"
    if key in seen:
        conflicts.append({"interface": iface, "table_id": tid, "reason": "duplicate_table_same_iface"})
    seen[key] = True
print(json.dumps(conflicts))
PY
}
