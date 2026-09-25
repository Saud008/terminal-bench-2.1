#!/usr/bin/env bash
set -euo pipefail

apply_deps_closure() {
  local symbols_json="$1"
  local deps_json="$2"
  python3 - <<'PY' "$symbols_json" "$deps_json"
import json, sys

symbols = json.loads(sys.argv[1])
deps = json.loads(sys.argv[2])
requires = deps.get("requires", {})
implies = deps.get("implies", {})
selects = deps.get("selects", {})

def is_enabled(val):
    return val in ("y", "m")

changed = True
while changed:
    changed = False
    for sym, val in list(symbols.items()):
        if not is_enabled(val):
            continue
        for req in requires.get(sym, []):
            if symbols.get(req) != "y":
                symbols[req] = "y"
                changed = True
print(json.dumps(symbols, sort_keys=True))
PY
}
