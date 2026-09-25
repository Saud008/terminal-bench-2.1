#!/usr/bin/env bash

# NSEC chain validation across merged include units.
validate_nsec_chain() {
  local units_json="$1"
  python3 - "$units_json" <<'PY'
import json, sys

units = json.loads(sys.argv[1])
broken = []
for unit in units:
    nsec = [r for r in unit.get("records", []) if r["type"] == "NSEC"]
    if len(nsec) < 2:
        continue
    for i in range(len(nsec) - 1):
        cur = nsec[i]
        nxt = nsec[i + 1]
        parts = cur["rdata"].split()
        if not parts or parts[0] != nxt["owner"]:
            broken.append({"file": unit["file"], "owner": cur["owner"], "expected": nxt["owner"], "got": parts[0] if parts else None})
print(json.dumps({"valid": len(broken) == 0, "breaks": broken}))
PY
}
