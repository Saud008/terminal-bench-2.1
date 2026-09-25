#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/crpe91/bucket/traverse.sh"
source "${APP_ROOT}/internal/crpe91/osd/filter_status.sh"
source "${APP_ROOT}/internal/crpe91/weight/normalize.sh"
source "${APP_ROOT}/internal/crpe91/rule/apply_steps.sh"

trace_pg_placement() {
  local loaded="$1"
  local pg_num="$2"
  python3 - <<'PY' "$loaded" "$pg_num"
import hashlib, json, sys
loaded = json.loads(open(sys.argv[1]).read())
pg_num = int(sys.argv[2])
pool = loaded["pool"]
rules = loaded["crush"]["rules"]
rule = next(r for r in rules if int(r["id"]) == int(pool["crush_rule"]))
def crush_hash(pg, item, retry):
    s = f"{pg}.{item}.{retry}"
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)
acting = []
steps = []
for st in sorted(rule["steps"], key=lambda s: s["op"], reverse=True):
    if st["op"] == "take":
        steps.append({"op": "take", "bucket": st["arg"]})
    elif st["op"] == "emit":
        steps.append({"op": "emit", "acting_set": acting})
    elif st["op"] == "chooseleaf":
        acting.append(0)
pool_id = int(pool["id"])
print(json.dumps({
    "pg_id": f"{pool_id}.{pg_num:x}",
    "pool_id": pool_id,
    "pg_num": pg_num,
    "primary_osd": acting[0] if acting else -1,
    "acting_set": acting,
    "steps": steps,
}))
PY
}
