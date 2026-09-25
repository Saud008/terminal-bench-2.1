#!/usr/bin/env bash
# Baseline sort is name-only ascending.
set -euo pipefail
python3 -c '
import json, sys
rows = json.loads(sys.stdin.read())
rows.sort(key=lambda r: r["name"])
for i, r in enumerate(rows, 1):
    r["reclaim_rank"] = i
json.dump(rows, sys.stdout)
'
