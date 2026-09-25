#!/usr/bin/env bash

WORK="/app/work"
TREE="${WORK}/tree"
STATE="${WORK}/state.json"

json_get() {
  local file="$1"
  local key="$2"
  python3 - "$file" "$key" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
key = sys.argv[2]
cur = doc
for part in key.split("."):
    if isinstance(cur, dict):
        cur = cur.get(part)
    else:
        cur = None
        break
if cur is None:
    sys.exit(1)
if isinstance(cur, bool):
    print("true" if cur else "false")
else:
    print(cur)
PY
}

copy_scenario_tree() {
  local scenario_dir="$1"
  rm -rf "${TREE}"
  mkdir -p "${TREE}"
  if [[ -f "${scenario_dir}/tree.json" ]]; then
    cp "${scenario_dir}/tree.json" "${TREE}/tree.json"
  fi
}

effective_now() {
  if [[ -n "${TB3_CLOCK_EPOCH:-}" ]]; then
    echo "${TB3_CLOCK_EPOCH}"
  else
    echo "${NOW_EPOCH}"
  fi
}

normalize_path() {
  python3 - "$1" <<'PY'
import os, sys
print(os.path.normpath(sys.argv[1]))
PY
}
