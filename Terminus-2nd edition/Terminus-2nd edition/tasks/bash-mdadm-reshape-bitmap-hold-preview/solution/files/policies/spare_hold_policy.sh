#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
holds = set(inv.get("spare_holds") or [])
blocked = {}
for arr in inv.get("arrays", []):
    spares = arr.get("spares") or []
    if any(s in holds for s in spares):
        blocked[arr["name"]] = "blocked_spare_hold"
json.dump(blocked, sys.stdout)
PY
