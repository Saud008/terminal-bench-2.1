#!/usr/bin/env bash
# Moved resource before-tag lineage resolution.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/inherit.sh"

effective_before_tags_json() {
  local row_json="$1"
  local plan_path="$2"
  local policy_path="$3"
  python3 - "${row_json}" "${plan_path}" "${policy_path}" <<'PY'
import json, sys
from pathlib import Path

row = json.loads(sys.argv[1])
plan = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
policy = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
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

def module_defaults(address, tags):
    merged = dict(tags)
    applicable = []
    for entry in policy.get("module_defaults", []):
        prefix = entry.get("module_prefix", "")
        if not prefix:
            continue
        if address == prefix or address.startswith(prefix + "."):
            canon = to_canon(entry.get("tags"))
            applicable.append((len(prefix), canon))
    applicable.sort(key=lambda r: r[0])
    for _, canon in applicable:
        for key, value in canon.items():
            if key not in merged:
                merged[key] = value
    return merged

idx = {r["address"]: r for r in plan.get("resource_changes", [])}
address = row["address"]
before_raw = (row.get("change", {}).get("before") or {})
tags = to_canon(before_raw.get("tags"))
actions = row.get("change", {}).get("actions", [])
if "move" in actions:
    prev = row.get("previous_address")
    if prev and prev in idx:
        prev_before = idx[prev].get("change", {}).get("before") or {}
        prev_tags = to_canon(prev_before.get("tags"))
        for key, value in prev_tags.items():
            if key not in tags:
                tags[key] = value
print(json.dumps(module_defaults(address, tags), sort_keys=True))
PY
}
