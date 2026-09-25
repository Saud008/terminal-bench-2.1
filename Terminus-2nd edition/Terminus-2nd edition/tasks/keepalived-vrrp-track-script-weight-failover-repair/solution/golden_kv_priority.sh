#!/usr/bin/env bash
# Role transitions — records previous role for advert counter.

kv_update_role() {
  local staging_path="$1"
  python3 - "${staging_path}" <<'PY'
import json, sys
staging = json.load(open(sys.argv[1], encoding="utf-8"))
threshold = int(staging["master_threshold"])
effective = int(staging["effective_priority"])
prev = staging["role"]
staging["_prev_role"] = prev
new_role = "MASTER" if effective >= threshold else "BACKUP"
staging["role"] = new_role
if prev != new_role:
    staging["notify_pending"] = True
    staging["notify_complete"] = False
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
PY
}
