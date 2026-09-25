#!/usr/bin/env bash
# Baseline power-sequence gate ignores the off_first disconnect requirement.
set -euo pipefail
python3 - <<'PY'
import json, sys
blocked = {}
json.dump(blocked, sys.stdout)
PY
