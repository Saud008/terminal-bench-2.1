#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

parse_readings_json() {
  local readings_path="$1"
  require_file "${readings_path}"
  python3 - "${readings_path}" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
patches = {}
for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split("\t")
    if len(parts) < 4:
        continue
    patch_id, l_s, a_s, b_s = parts[0], parts[1], parts[2], parts[3]
    if patch_id == "patch_id" or l_s == "L":
        continue
    try:
        l_val = float(l_s)
        a_val = float(a_s)
        b_val = float(b_s)
    except ValueError:
        continue
    batch_id = parts[4] if len(parts) > 4 else ""
    patches[patch_id] = {
        "patch_id": patch_id,
        "L": l_val,
        "a": a_val,
        "b": b_val,
        "batch_id": batch_id,
    }
ordered = [patches[k] for k in sorted(patches)]
print(json.dumps(ordered, separators=(",", ":")))
PY
}
