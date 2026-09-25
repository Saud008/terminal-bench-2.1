#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/xk7r/b01/common.sh"

scenario=""
run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) scenario="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown $1" >&2; exit 2 ;;
  esac
done
[[ -n "$scenario" && -n "$run_id" ]] || exit 2

root="${TB3_SCENARIO_ROOT:-${APP_ROOT}/fixtures/scenarios}"
base="${root}/${scenario}"
readings="${base}/readings.tsv"
digest=$(sha256_file "$readings")

rows=$(python3 - <<'PY' "$readings"
import csv, json, sys
from pathlib import Path
path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines()
header = lines[0].split("\t")
seen = {}
for line in lines[1:]:
    if not line.strip():
        continue
    parts = line.split("\t")
    row = dict(zip(header, parts))
    seen[row["reading_id"]] = row
out = []
for rid in sorted(seen, key=lambda x: (seen[x]["batch_id"], x)):
    r = seen[rid]
    out.append({
        "batch_id": r["batch_id"],
        "reading_id": r["reading_id"],
        "L": float(r["L"]),
        "a": float(r["a"]),
        "b": float(r["b"]),
        "measured_at_epoch": int(r["measured_at_epoch"]),
        "spectrometer_id": r["spectrometer_id"],
    })
print(json.dumps(out))
PY
)

mkdir -p "$CORR_SNAP_DIR"
jq -n --arg run_id "$run_id" --arg scenario "$scenario" --arg digest "$digest" --argjson rows "$rows" \
  '{run_id: $run_id, scenario: $scenario, readings_digest: $digest, correlated: false, rows: $rows, correlation_digest: null}' \
  > "${CORR_SNAP_DIR}/${run_id}.json"
echo "${run_id}|${digest}" >> "$REGISTRY"
echo "ingested ${scenario} as ${run_id}"
