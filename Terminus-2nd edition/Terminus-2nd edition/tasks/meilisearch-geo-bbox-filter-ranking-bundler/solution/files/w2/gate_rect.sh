#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/level-roster.json").read_text())
w = inv["window"]; blocked = {}
for doc in inv.get("documents", []):
    if doc.get("kind") != "document":
        continue
    lon, lat = float(doc["lon"]), float(doc["lat"])
    inside = float(w["min_lon"]) <= lon <= float(w["max_lon"]) and float(w["min_lat"]) <= lat <= float(w["max_lat"])
    if not inside:
        blocked[doc["doc_id"]] = "blocked_bbox"
json.dump(blocked, sys.stdout)
PY
