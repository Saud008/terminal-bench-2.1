#!/usr/bin/env bash
# BROKEN baseline: move lineage from previous_address is not applied.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/inherit.sh"

effective_before_tags_json() {
  local row_json="$1"
  local plan_path="$2"
  local policy_path="$3"
  python3 - "${row_json}" "${policy_path}" <<'PY'
import json, sys

row = json.loads(sys.argv[1])
policy = json.loads(open(sys.argv[2], encoding="utf-8").read())
rev = {v: k for k, v in policy.get("tag_key_map", {}).items()}

def to_canon(tags):
    out = {}
    for display, value in (tags or {}).items():
        if value is None:
            continue
        key = rev.get(str(display))
        if key:
            out[key] = str(value)
    return out

before_raw = row.get("change", {}).get("before") or {}
tags = to_canon(before_raw.get("tags"))
print(json.dumps(tags, sort_keys=True))
PY
}
