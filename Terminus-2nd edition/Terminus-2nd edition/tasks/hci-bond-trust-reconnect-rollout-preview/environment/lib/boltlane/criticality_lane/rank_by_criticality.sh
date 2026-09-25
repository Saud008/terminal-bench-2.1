#!/usr/bin/env bash
# Baseline sort is mac-only ascending, ignoring criticality.
set -euo pipefail
python3 -c '
import json, sys
rows = json.loads(sys.stdin.read())
rows.sort(key=lambda r: r["mac"])
json.dump(rows, sys.stdout)
'
