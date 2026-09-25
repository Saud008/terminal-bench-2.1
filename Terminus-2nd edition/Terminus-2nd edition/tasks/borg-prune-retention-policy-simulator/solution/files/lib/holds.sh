#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

holds_match_name() {
  local name="$1"
  local holds_json="$2"
  python3 - "${name}" "${holds_json}" <<'PY'
import json, sys
name, holds_path = sys.argv[1], sys.argv[2]
holds = json.loads(open(holds_path, encoding="utf-8").read())
if name in holds.get("exact", []):
    print("yes")
    raise SystemExit(0)
for prefix in holds.get("prefix", []):
    if name.startswith(prefix):
        print("yes")
        raise SystemExit(0)
print("no")
PY
}
