#!/usr/bin/env bash

age_token_to_seconds() {
  local token="$1"
  python3 - "$token" <<'PY'
import sys
token = sys.argv[1]
if token.isdigit():
    print(int(token))
    raise SystemExit
num = int(token[:-1])
unit = token[-1]
mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
print(num * mult)
PY
}

path_age_eligible() {
  local path="$1"
  local age_sec="$2"
  local now_epoch="$3"
  local tree_file="$4"
  python3 - "$path" "$age_sec" "$now_epoch" "$tree_file" <<'PY'
import json, sys
path, age_sec, now, tree_file = sys.argv[1:5]
age_sec = int(age_sec)
now = int(now)
doc = json.load(open(tree_file, encoding="utf-8"))
meta = doc["paths"].get(path)
if not meta:
    print("false")
    raise SystemExit
stamp = int(meta.get("mtime", 0))
print("true" if now - stamp >= age_sec else "false")
PY
}
