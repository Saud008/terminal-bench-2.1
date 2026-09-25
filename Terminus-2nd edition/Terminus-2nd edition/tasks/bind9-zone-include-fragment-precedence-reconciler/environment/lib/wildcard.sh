#!/usr/bin/env bash

# Wildcard apex overlap checks for merged zone records.
detect_wildcard_apex_overlap() {
  local records_json="$1"
  python3 - "$records_json" <<'PY'
import json, sys

records = json.loads(sys.argv[1])
origin = records[0].get("origin", "") if records else ""
wildcards = [r for r in records if r["owner"].startswith("*")]
conflicts = []
for w in wildcards:
    for r in records:
        if r["owner"] == "@" or r["owner"] == origin.rstrip("."):
            conflicts.append({"wildcard": w["owner"], "apex": r["owner"], "type": r["type"]})
print(json.dumps(conflicts))
PY
}
