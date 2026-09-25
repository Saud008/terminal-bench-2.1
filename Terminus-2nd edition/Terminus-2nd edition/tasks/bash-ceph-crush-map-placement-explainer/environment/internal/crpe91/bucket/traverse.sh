#!/usr/bin/env bash
set -euo pipefail

list_hosts_under_root() {
  local crush="$1"
  local root_name="$2"
  python3 - <<'PY' "$crush" "$root_name"
import json, sys
crush = json.loads(sys.argv[1])
root_name = sys.argv[2]
bmap = {int(b["id"]): b for b in crush["buckets"]}
by_name = {b["name"]: b for b in crush["buckets"]}
root = by_name[root_name]
hosts = []
for child in root.get("children", []):
    bid = int(child["id"])
    b = bmap[bid]
    if b["type"] == "rack":
        hosts.append(b)
print(json.dumps(hosts))
PY
}
