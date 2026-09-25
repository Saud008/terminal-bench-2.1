#!/usr/bin/env bash
# BROKEN baseline: skips module default inheritance.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

apply_module_defaults_json() {
  local address="$1"
  local tags_json="$2"
  local policy_path="$3"
  echo "${tags_json}"
}

display_tags_to_canonical_json() {
  local tags_json="$1"
  local policy_path="$2"
  python3 - "${tags_json}" "${policy_path}" <<'PY'
import json, sys
raw = json.loads(sys.argv[1])
policy = json.loads(open(sys.argv[2], encoding="utf-8").read())
rev = {v: k for k, v in policy.get("tag_key_map", {}).items()}
out = {}
for display, value in (raw or {}).items():
    if value is None:
        continue
    key = rev.get(str(display))
    if key:
        out[key] = str(value)
print(json.dumps(out, sort_keys=True))
PY
}
