#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
MIN_ACTIVE = {"raid1": 1, "raid5": 3, "raid6": 4, "raid10": 2}
inv = json.loads(Path("/app/state/inventory.json").read_text())
blocked = {}
for arr in inv.get("arrays", []):
    level = arr.get("level")
    minimum = MIN_ACTIVE.get(level)
    if minimum is not None and int(arr.get("active_disks", 0)) < minimum:
        blocked[arr["name"]] = "blocked_degraded"
json.dump(blocked, sys.stdout)
PY
