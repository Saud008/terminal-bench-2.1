#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
blocked = {}
for bk in inv.get("bookmarks", []):
    target = bk.get("target")
    if target:
        blocked[target] = "blocked_bookmark"
json.dump(blocked, sys.stdout)
PY
