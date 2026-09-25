#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../osd/filter_status.sh"

normalize_sibling_weights() {
  local json_rows="$1"
  python3 - <<'PY' "$json_rows"
import json, sys
rows = json.loads(sys.argv[1])
total = sum(float(r.get("weight", 0)) for r in rows)
if total <= 0:
    print("[]")
    raise SystemExit
scale = 65536.0 / total
out = []
for r in rows:
    out.append({"id": r["id"], "norm_weight": int(float(r.get("weight", 0)) * scale)})
print(json.dumps(out))
PY
}
