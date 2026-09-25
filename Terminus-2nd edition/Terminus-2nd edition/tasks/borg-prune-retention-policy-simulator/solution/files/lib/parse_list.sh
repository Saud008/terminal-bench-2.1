#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

parse_list_to_json() {
  local list_file="$1"
  python3 - "${list_file}" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
archives = {}
line_no = 0
for raw in path.read_text(encoding="utf-8").splitlines():
    line_no += 1
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split("\t")
    if len(parts) < 4:
        continue
    name, ts, size, seg = parts[0], parts[1], parts[2], parts[3]
    archives[name] = {
        "name": name,
        "ts": ts,
        "bytes": int(size),
        "segments": int(seg),
        "line": line_no,
    }
rows = sorted(archives.values(), key=lambda a: (a["ts"], a["line"]))
print(json.dumps(rows, sort_keys=True, separators=(",", ":")))
PY
}
