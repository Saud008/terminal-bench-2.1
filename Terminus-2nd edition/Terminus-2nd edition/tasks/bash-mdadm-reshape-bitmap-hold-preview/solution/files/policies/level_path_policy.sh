#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
ALLOWED = {
    ("raid1", "raid5"),
    ("raid5", "raid6"),
    ("raid5", "raid1"),
    ("raid10", "raid10"),
}
inv = json.loads(Path("/app/state/inventory.json").read_text())
blocked = {}
for arr in inv.get("arrays", []):
    pair = (arr.get("level"), arr.get("target_level"))
    if pair not in ALLOWED:
        blocked[arr["name"]] = "blocked_illegal_path"
json.dump(blocked, sys.stdout)
PY
