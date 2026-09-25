#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/level-roster.json").read_text())
blocked = {}
for doc in inv.get("documents", []):
    if doc.get("kind") == "shard_marker" and (doc.get("filter_pins") or []):
        blocked[doc["doc_id"]] = "blocked_pin"
json.dump(blocked, sys.stdout)
PY
