#!/usr/bin/env bash
# Weight aggregation — floor applies to base plus active weights.

kv_compute_effective() {
  local staging_path="$1"
  python3 - "${staging_path}" <<'PY'
import json, sys
staging = json.load(open(sys.argv[1], encoding="utf-8"))
base = int(staging["base_priority"])
floor = int(staging["priority_floor"])
active = sum(int(m["weight_value"]) for m in staging["tracks"].values() if m["weight_active"])
effective = max(floor, base + active)
staging["effective_priority"] = effective
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
print(effective)
PY
}
