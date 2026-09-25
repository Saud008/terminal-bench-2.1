#!/usr/bin/env bash
set -euo pipefail
python3 -c '
import json, sys
rows = json.loads(sys.stdin.read())
rows.sort(key=lambda r: (-int(r["depth"]), int(r["creation_txg"]), r["name"]))
for i, r in enumerate(rows, 1):
    r["reclaim_rank"] = i
json.dump(rows, sys.stdout)
'
