#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
blocked = {}
for ds in inv.get("datasets", []):
    origin = ds.get("clone_of")
    if origin:
        blocked[origin] = "blocked_clone"
json.dump(blocked, sys.stdout)
PY
