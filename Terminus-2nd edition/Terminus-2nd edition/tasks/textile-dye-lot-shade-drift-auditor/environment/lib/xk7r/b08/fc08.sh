#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
CORR_SNAP_DIR="${APP_ROOT}/state/shade-correlation"

run_id=""
output=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" && -n "$output" ]] || exit 2

corr_snap="${CORR_SNAP_DIR}/${run_id}.json"
scenario=$(jq -r '.scenario' "$corr_snap")
root="${TB3_SCENARIO_ROOT:-${APP_ROOT}/fixtures/scenarios}"
readings="${root}/${scenario}/readings.tsv"

drift_rows=$(python3 - <<'PY' "$readings" "$corr_snap"
import csv, json, sys
from pathlib import Path
corr_snap = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
st_map = {(r["batch_id"], r["reading_id"]): r for r in corr_snap.get("rows", [])}
lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
header = lines[0].split("\t")
out = []
for line in lines[1:]:
    if not line.strip():
        continue
    row = dict(zip(header, line.split("\t")))
    key = (row["batch_id"], row["reading_id"])
    if key not in st_map:
        continue
    s = st_map[key]
    out.append({
        "batch_id": s["batch_id"],
        "reading_id": s["reading_id"],
        "delta_e": s.get("delta_e", 0),
        "drift_class": s.get("drift_class", "within"),
        "recipe_version": s.get("recipe_version", ""),
        "rework_applied": s.get("rework_applied", False),
    })
out.sort(key=lambda r: (r["batch_id"], r["reading_id"]))
print(json.dumps(out))
PY
)

audit=$(echo "$drift_rows" | sha256sum | awk '{print $1}')
jq -n --arg run_id "$run_id" --argjson drift_rows "$drift_rows" --arg audit "$audit" \
  '{run_id: $run_id, drift_rows: $drift_rows, totals: {row_count: ($drift_rows|length)}, audit_digest: $audit}' > "$output"
echo "exported ${run_id}"
