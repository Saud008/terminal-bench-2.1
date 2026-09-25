#!/usr/bin/env bash
# Peak slot / concurrency helpers.
set -euo pipefail

peak_concurrency_from_pardir() {
  local par_dir="$1"
  python3 - "${par_dir}" <<'PY'
import sys
from pathlib import Path
par_dir = Path(sys.argv[1])
max_slot = 0
for par in par_dir.glob("*.par"):
    data = {}
    for line in par.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    if "slot" in data:
        max_slot = max(max_slot, int(data["slot"]))
print(max_slot)
PY
}

peak_concurrency_from_db() {
  sqlite3 "${MANIFEST_DB}" "SELECT COALESCE(MAX(slot), 0) FROM jobs;"
}
