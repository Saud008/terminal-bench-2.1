#!/usr/bin/env bash

normalize_value() {
  local raw="$1"
  python3 - "$raw" <<'PY'
import sys

v = sys.argv[1]
if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
    inner = v[1:-1]
    inner = inner.replace('\\"', '"')
    print(inner)
else:
    print(v)
PY
}
