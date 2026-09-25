#!/usr/bin/env bash
# Computed unknown tag detection.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/inherit.sh"

KNOWN_AFTER='(known after apply)'

effective_after_tags_json() {
  local row_json="$1"
  local policy_path="$2"
  python3 - "${row_json}" "${policy_path}" "${KNOWN_AFTER}" <<'PY'
import json, sys

row = json.loads(sys.argv[1])
policy = json.loads(open(sys.argv[2], encoding="utf-8").read())
known_after = sys.argv[3]
rev = {v: k for k, v in policy.get("tag_key_map", {}).items()}

def module_defaults(address, tags):
    merged = dict(tags)
    applicable = []
    for entry in policy.get("module_defaults", []):
        prefix = entry.get("module_prefix", "")
        if not prefix:
            continue
        if address == prefix or address.startswith(prefix + "."):
            canon = {}
            for display, value in (entry.get("tags") or {}).items():
                key = rev.get(str(display))
                if key:
                    canon[key] = str(value)
            applicable.append((len(prefix), canon))
    applicable.sort(key=lambda r: r[0])
    for _, canon in applicable:
        for key, value in canon.items():
            if key not in merged:
                merged[key] = value
    return merged

after_raw = row.get("change", {}).get("after") or {}
raw = after_raw.get("tags") or {}
unknown = []
known = {}
for display, value in raw.items():
    if value is None:
        continue
    key = rev.get(str(display))
    if not key:
        continue
    text = str(value)
    if text == known_after:
        unknown.append(key)
    else:
        known[key] = text
merged = module_defaults(row["address"], known)
print(json.dumps({"tags": merged, "unknown": sorted(unknown)}, sort_keys=True))
PY
}
