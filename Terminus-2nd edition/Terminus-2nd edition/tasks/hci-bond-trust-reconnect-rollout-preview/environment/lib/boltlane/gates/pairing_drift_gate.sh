#!/usr/bin/env bash
# Baseline pairing gate never inspects addr_type mismatch or pairing_confirmed.
set -euo pipefail
python3 - <<'PY'
import json, sys
blocked = {}
json.dump(blocked, sys.stdout)
PY
