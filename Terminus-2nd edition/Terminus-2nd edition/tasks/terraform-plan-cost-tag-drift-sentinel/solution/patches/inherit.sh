#!/usr/bin/env bash
# Module default tag inheritance.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

apply_module_defaults_json() {
  local address="$1"
  local tags_json="$2"
  local policy_path="$3"
  python3 - "${address}" "${tags_json}" "${policy_path}" <<'PY'
import json, sys

address = sys.argv[1]
tags = json.loads(sys.argv[2])
policy = json.loads(open(sys.argv[3], encoding="utf-8").read())
rev = {v: k for k, v in policy.get("tag_key_map", {}).items()}

def prefixes(addr: str) -> list[str]:
    parts = addr.split(".")
    out: list[str] = []
    if not parts or parts[0] != "module":
        return out
    for i in range(len(parts) - 1):
        if parts[i] == "module" and i + 1 < len(parts):
            out.append(".".join(parts[: i + 2]))
    return out

mods = []
for entry in policy.get("module_defaults", []):
    prefix = entry.get("module_prefix", "")
    if not prefix:
        continue
    if address == prefix or address.startswith(prefix + "."):
        canon = {}
        for display, value in (entry.get("tags") or {}).items():
            key = rev.get(display)
            if key:
                canon[key] = str(value)
        mods.append((len(prefix), canon))
mods.sort(key=lambda row: row[0])
merged = dict(tags)
for _, canon in mods:
    for key, value in canon.items():
        if key not in merged:
            merged[key] = value
print(json.dumps(merged, sort_keys=True))
PY
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
