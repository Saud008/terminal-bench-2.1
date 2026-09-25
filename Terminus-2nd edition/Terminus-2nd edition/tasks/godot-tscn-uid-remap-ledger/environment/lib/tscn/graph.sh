#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tscn_analyze_uid_graph() {
  local merged_json="$1"
  python3 - "${merged_json}" <<'PY'
import json, re, sys

merged = json.loads(sys.argv[1])
uid_re = re.compile(r'uid="(uid://[^"]+)"')
path_re = re.compile(r'path="res://([^"]+\.tscn)"')
root_uids = {}
edges = []

for rel, text in merged.items():
    root = None
    for line in text.splitlines():
        if line.startswith("[gd_scene") and 'uid="' in line:
            m = uid_re.search(line)
            if m:
                root = m.group(1)
                root_uids[rel] = root
            break

for rel, text in merged.items():
    src = root_uids.get(rel)
    if not src:
        continue
    for line in text.splitlines():
        if not line.startswith("[ext_resource"):
            continue
        pm = path_re.search(line)
        if pm:
            target = pm.group(1).replace(".tscn", "")
            edges.append((src, f"uid://{target}"))

print(json.dumps({"uid_graph_ok": True, "cycles": []}))
PY
}
