#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../osd/filter_status.sh"

normalize_sibling_weights() {
  local json_rows="$1"
  python3 - <<'PY' "$json_rows"
import json, sys
rows = json.loads(sys.argv[1])
eligible = [r for r in rows if r.get("eligible", True)]
total = sum(float(r.get("eff_weight", r.get("weight", 0))) for r in eligible)
if total <= 0:
    print("[]")
    raise SystemExit
scale = 65536.0 / total
out = []
for r in eligible:
    w = float(r.get("eff_weight", r.get("weight", 0)))
    out.append({"id": r["id"], "norm_weight": int(w * scale)})
print(json.dumps(out))
PY
}
