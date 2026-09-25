#!/usr/bin/env bash
# Advert counter — reset on master demotion; increment only while MASTER.

kv_bump_advert() {
  local staging_path="$1"
  python3 - "${staging_path}" <<'PY'
import json, sys
staging = json.load(open(sys.argv[1], encoding="utf-8"))
prev = staging.get("_prev_role", staging["role"])
role = staging["role"]
if prev == "MASTER" and role == "BACKUP":
    staging["advert_seq"] = 0
elif role == "MASTER":
    staging["advert_seq"] = int(staging.get("advert_seq", 0)) + 1
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
PY
}
