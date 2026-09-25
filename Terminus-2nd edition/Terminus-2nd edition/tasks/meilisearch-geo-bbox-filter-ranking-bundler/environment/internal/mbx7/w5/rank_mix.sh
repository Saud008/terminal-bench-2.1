#!/usr/bin/env bash
set -euo pipefail
python3 -c '
import json, sys
rows = json.loads(sys.stdin.read())
rows.sort(key=lambda r: (float(r["affinity"]), int(r.get("capture_seq", 0))))
for i, r in enumerate(rows, 1):
    r["admit_rank"] = i
json.dump(rows, sys.stdout)
'
