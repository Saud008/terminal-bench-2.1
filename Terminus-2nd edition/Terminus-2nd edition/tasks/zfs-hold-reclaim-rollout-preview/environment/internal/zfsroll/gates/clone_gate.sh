#!/usr/bin/env bash
# Baseline clone gate is a no-op.
set -euo pipefail
python3 - <<'PY'
import json, sys
json.dump({}, sys.stdout)
PY
