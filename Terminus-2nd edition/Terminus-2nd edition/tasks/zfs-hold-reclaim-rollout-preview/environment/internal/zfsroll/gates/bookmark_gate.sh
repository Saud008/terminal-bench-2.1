#!/usr/bin/env bash
# Baseline bookmark gate blocks bookmark names instead of targets.
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
blocked = {}
for bk in inv.get("bookmarks", []):
    blocked[bk["name"]] = "blocked_bookmark"
json.dump(blocked, sys.stdout)
PY
