#!/usr/bin/env bash

ROAM_APP_ROOT="${ROAM_APP_ROOT:-/app}"

roam_read_json_file() {
  local path="$1"
  python3 - "$path" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    print(json.dumps(json.load(fh)))
PY
}

roam_write_json_file() {
  local path="$1"
  local payload="$2"
  python3 - "$path" "$payload" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(sys.argv[2])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
