#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
window_hours = float(inv["window_hours"])
blocked = {}
for arr in inv.get("arrays", []):
    if float(arr.get("estimated_hours", 0)) > window_hours:
        blocked[arr["name"]] = "blocked_window"
json.dump(blocked, sys.stdout)
PY
