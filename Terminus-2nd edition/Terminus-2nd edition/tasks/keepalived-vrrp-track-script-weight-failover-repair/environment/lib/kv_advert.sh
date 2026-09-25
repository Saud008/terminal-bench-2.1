#!/usr/bin/env bash
# VRRP advert sequence counter.

kv_bump_advert() {
  local staging_path="$1"
  python3 - "${staging_path}" <<'PY'
import json, sys
staging = json.load(open(sys.argv[1], encoding="utf-8"))
staging["advert_seq"] = int(staging.get("advert_seq", 0)) + 1
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
PY
}
