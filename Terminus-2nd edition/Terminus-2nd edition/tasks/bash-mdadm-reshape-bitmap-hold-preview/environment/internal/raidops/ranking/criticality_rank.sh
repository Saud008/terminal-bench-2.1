#!/usr/bin/env bash
set -euo pipefail
python3 -c '
import json, sys
rows = json.loads(sys.stdin.read())
rows.sort(key=lambda r: r["name"])
json.dump(rows, sys.stdout)
'
