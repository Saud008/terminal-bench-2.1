#!/usr/bin/env bash
# Baseline hold gate only inspects filesystem holds.
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
blocked = {}
for ds in inv.get("datasets", []):
    if ds.get("kind") == "filesystem" and (ds.get("holds") or []):
        blocked[ds["name"]] = "blocked_hold"
json.dump(blocked, sys.stdout)
PY
