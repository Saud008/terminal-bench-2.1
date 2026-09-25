#!/usr/bin/env bash
# FetchContent closure collector (broken: root list file only).

fetch_collect_names() {
  local tree_json="$1"
  python3 - <<PY
import json
tree=json.load(open("${tree_json}"))
root=tree["files"][0]
names=sorted({d["name"] for d in root.get("fetchcontent", [])})
print(json.dumps(names))
PY
}
