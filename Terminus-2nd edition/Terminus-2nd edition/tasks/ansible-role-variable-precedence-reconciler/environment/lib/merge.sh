#!/usr/bin/env bash

apply_var_layer() {
  local base="$1"
  local overlay="$2"
  local behaviour="$3"
  python3 - "$base" "$overlay" "$behaviour" <<'PY'
import json, sys

def replace(base, overlay):
    out = dict(base)
    out.update(overlay)
    return out

base = json.loads(sys.argv[1])
overlay = json.loads(sys.argv[2])
print(json.dumps(replace(base, overlay), sort_keys=True))
PY
}
