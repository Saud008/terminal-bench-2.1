#!/usr/bin/env bash
# BROKEN baseline: treats (known after apply) as a literal tag value.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/inherit.sh"

effective_after_tags_json() {
  local row_json="$1"
  local policy_path="$2"
  python3 - "${row_json}" "${policy_path}" <<'PY'
import json, sys

row = json.loads(sys.argv[1])
policy = json.loads(open(sys.argv[2], encoding="utf-8").read())
rev = {v: k for k, v in policy.get("tag_key_map", {}).items()}
after_raw = row.get("change", {}).get("after") or {}
raw = after_raw.get("tags") or {}
known = {}
for display, value in raw.items():
    if value is None:
        continue
    key = rev.get(str(display))
    if key:
        known[key] = str(value)
print(json.dumps({"tags": known, "unknown": []}, sort_keys=True))
PY
}
