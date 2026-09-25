#!/usr/bin/env bash

recreate_allowed() {
  local z_path="$1"
  local pending_removals_json="$2"
  python3 - "$z_path" "$pending_removals_json" <<'PY'
import json, sys, os
z_path = sys.argv[1]
pending = json.loads(sys.argv[2])
print("true")
PY
}

apply_recreate() {
  local z_path="$1"
  local mode="$2"
  local user="$3"
  local group="$4"
  local tree_file="$5"
  python3 - "$z_path" "$mode" "$user" "$group" "$tree_file" <<'PY'
import json, sys
path, mode, user, group, tree = sys.argv[1:6]
doc = json.load(open(tree, encoding="utf-8"))
doc["paths"][path] = {
    "kind": "d" if mode.startswith("0") and mode[1] in "234567" else "f",
    "mode": mode,
    "user": user,
    "group": group,
    "atime": 0,
    "btime": 0,
    "mtime": 0,
}
json.dump(doc, open(tree, "w", encoding="utf-8"))
PY
}
