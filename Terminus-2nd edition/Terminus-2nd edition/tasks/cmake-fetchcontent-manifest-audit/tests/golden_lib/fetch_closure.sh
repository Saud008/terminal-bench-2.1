#!/usr/bin/env bash
# FetchContent closure collector (golden: all tree files).

fetch_collect_names() {
  local tree_json="$1"
  python3 - <<PY
import json
tree = json.load(open("${tree_json}", encoding="utf-8"))
names = sorted({
    d["name"]
    for f in tree.get("files", [])
    for d in f.get("fetchcontent", [])
})
print(json.dumps(names))
PY
}
