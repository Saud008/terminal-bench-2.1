#!/usr/bin/env bash
# Partial WAL segment handling.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

list_partial_files() {
  local archive="$1"
  find "${archive}" -maxdepth 1 -type f -name '*.partial' -printf '%f\n' | sort
}

partial_blocks_restore() {
  local archive="$1"
  local selected="$2"
  python3 - "${archive}" "${selected}" <<'PY'
import json, sys
from pathlib import Path
archive = Path(sys.argv[1])
selected = sys.argv[2].upper()
sel_tl = int(selected[0:8], 16)
sel_seg = int(selected[8:24], 16)
blocked = []
for path in sorted(archive.glob("*.partial")):
    base = path.name[:-8]
    tl = int(base[0:8], 16)
    seg = int(base[8:24], 16)
    if tl == sel_tl and seg <= sel_seg:
        blocked.append(path.name)
print(json.dumps(blocked, separators=(",", ":")))
PY
}
