#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/level-roster.json").read_text())
json.dump({"doc_floor": int(inv["doc_floor"])}, sys.stdout)
PY
