#!/usr/bin/env bash
# Baseline pool floor treats equality as healthy.
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
free_pct = float(inv["free_pct"])
floor_pct = float(inv["floor_pct"])
ok = free_pct >= floor_pct
json.dump({"floor_ok": ok}, sys.stdout)
PY
