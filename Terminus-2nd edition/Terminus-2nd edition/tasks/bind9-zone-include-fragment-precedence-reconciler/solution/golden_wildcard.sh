#!/usr/bin/env bash

detect_wildcard_apex_overlap() {
  local records_json="$1"
  local origin="$2"
  python3 - "$records_json" "$origin" <<'PY'
import json, sys

records = json.loads(sys.argv[1])
origin = sys.argv[2].rstrip(".")
wildcards = [r for r in records if r["owner"].startswith("*")]
conflicts = []
for w in wildcards:
    for r in records:
        if r["owner"] in ("@", origin) and r["type"] in ("A", "AAAA"):
            conflicts.append({"wildcard": w["owner"], "apex": r["owner"], "type": r["type"]})
print(json.dumps(conflicts))
PY
}
