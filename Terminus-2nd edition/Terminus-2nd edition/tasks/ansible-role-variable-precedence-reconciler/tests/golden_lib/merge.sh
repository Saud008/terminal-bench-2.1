#!/usr/bin/env bash

apply_var_layer() {
  local base="$1"
  local overlay="$2"
  local behaviour="$3"
  python3 - "$base" "$overlay" "$behaviour" <<'PY'
import json, sys

def deep_merge(base, overlay):
    out = dict(base)
    for key, value in overlay.items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(value, dict)
        ):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out

def replace(base, overlay):
    out = dict(base)
    out.update(overlay)
    return out

base = json.loads(sys.argv[1])
overlay = json.loads(sys.argv[2])
behaviour = sys.argv[3]
if behaviour == "merge":
    result = deep_merge(base, overlay)
else:
    result = replace(base, overlay)
print(json.dumps(result, sort_keys=True))
PY
}
