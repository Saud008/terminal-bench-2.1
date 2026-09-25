#!/usr/bin/env bash

apply_ownership() {
  local path="$1"
  local mode="$2"
  local user="$3"
  local group="$4"
  local tree_file="$5"
  python3 - "$path" "$mode" "$user" "$group" "$tree_file" <<'PY'
import json, sys
path, mode, user, group, tree = sys.argv[1:6]
doc = json.load(open(tree, encoding="utf-8"))
if path not in doc["paths"]:
    print("missing")
    raise SystemExit
meta = doc["paths"][path]
meta["mode"] = mode
meta["user"] = user
meta["group"] = group
json.dump(doc, open(tree, "w", encoding="utf-8"))
print("ok")
PY
}

ownership_phase() {
  echo "before_remove"
}
