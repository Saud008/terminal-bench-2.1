#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
blocked = {}
for arr in inv.get("arrays", []):
    bitmap = arr.get("bitmap")
    clear_planned = bool(arr.get("bitmap_clear_planned"))
    if bitmap == "external" and not clear_planned:
        blocked[arr["name"]] = "blocked_bitmap"
json.dump(blocked, sys.stdout)
PY
