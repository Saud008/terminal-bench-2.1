#!/usr/bin/env bash

validate_nsec_chain() {
  local units_json="$1"
  python3 - "$units_json" <<'PY'
import json, sys

units = json.loads(sys.argv[1])
nsec = []
for unit in units:
    for rec in unit.get("records", []):
        if rec["type"] == "NSEC":
            nsec.append({**rec, "file": unit["file"]})
broken = []
for i in range(len(nsec) - 1):
    cur = nsec[i]
    nxt = nsec[i + 1]
    parts = cur["rdata"].split()
    expected = parts[0] if parts else ""
    if expected != nxt["owner"]:
        broken.append({"file": cur["file"], "owner": cur["owner"], "expected": nxt["owner"], "got": expected})
print(json.dumps({"valid": len(broken) == 0, "breaks": broken}))
PY
}
