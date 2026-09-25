#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/level-roster.json").read_text())
json.dump({"lag_ok": int(inv["lag_ms"]) < int(inv["lag_ceiling_ms"])}, sys.stdout)
PY
