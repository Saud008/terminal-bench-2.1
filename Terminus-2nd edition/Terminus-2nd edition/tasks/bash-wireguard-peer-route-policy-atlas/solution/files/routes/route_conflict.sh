#!/usr/bin/env bash
set -euo pipefail

detect_route_conflicts() {
  local routes_json="$1"
  python3 - <<'PY' "$routes_json"
import json, sys
routes = json.loads(sys.argv[1])
by_table = {}
conflicts = []
for block in routes:
    tid = block.get("table_id")
    iface = block.get("interface", "")
    if tid in by_table and by_table[tid] != iface:
        conflicts.append({
            "table_id": tid,
            "interface_a": by_table[tid],
            "interface_b": iface,
            "reason": "cross_interface_table_id",
        })
    elif tid not in by_table:
        by_table[tid] = iface
conflicts.sort(key=lambda c: (c["table_id"], c["interface_a"], c["interface_b"]))
print(json.dumps(conflicts))
PY
}
