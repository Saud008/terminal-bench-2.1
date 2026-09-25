#!/usr/bin/env bash
set -euo pipefail

normalized_fingerprint() {
  local loaded="$1"
  python3 - <<'PY' "$loaded"
import hashlib, json, sys
loaded = json.loads(open(sys.argv[1]).read())

def eff(o):
    return float(o["weight"]) * float(o.get("reweight", 1.0))

def eligible(o):
    return o.get("status") == "up" and o.get("in", True)

buckets = loaded["crush"]["buckets"]
osds = loaded["osd"]["osds"]
body = {
    "buckets": sorted(
        [{"id": b["id"], "name": b["name"], "type": b["type"], "children": b.get("children", [])} for b in buckets],
        key=lambda x: int(x["id"]),
    ),
    "eligible_osds": sorted(
        [{"id": o["id"], "eff_weight": eff(o)} for o in osds if eligible(o)],
        key=lambda x: int(x["id"]),
    ),
}
print(hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest())
PY
}
