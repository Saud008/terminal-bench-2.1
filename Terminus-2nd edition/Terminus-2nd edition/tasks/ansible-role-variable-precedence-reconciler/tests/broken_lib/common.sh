#!/usr/bin/env bash

VAR_LOADER="/app/tools/var_loader.py"
TOUCH_FILE="/app/output/.resolve-touch"

json_get() {
  local key="$1"
  local blob="$2"
  python3 - "$key" "$blob" <<'PY'
import json, sys
key, blob = sys.argv[1], sys.argv[2]
data = json.loads(blob)
print(data.get(key, ""))
PY
}

load_yaml_vars() {
  local path="$1"
  python3 "$VAR_LOADER" touch-load --file "$path" --touch "$TOUCH_FILE"
}

load_yaml_vars_quiet() {
  local path="$1"
  python3 "$VAR_LOADER" load --file "$path"
}

merge_shallow() {
  local base="$1"
  local overlay="$2"
  python3 - "$base" "$overlay" <<'PY'
import json, sys
base = json.loads(sys.argv[1])
overlay = json.loads(sys.argv[2])
base.update(overlay)
print(json.dumps(base, sort_keys=True))
PY
}
