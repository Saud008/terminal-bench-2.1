#!/usr/bin/env bash
# Apply bundle transitions.

set -euo pipefail

source /app/lib/common.sh
source /app/lib/ingest.sh
source /app/lib/dag.sh

write_staging() {
  local tree="$1"
  local bundle="$2"
  local bundle_id="$3"
  local state_dir="$4"
  local plan_json="$5"
  mkdir -p "${STATE}"
  python3 - "${plan_json}" "${bundle_id}" <<'PY' > "${STATE}/staging.json"
import json, sys
from pathlib import Path
plan = json.loads(Path(sys.argv[1]).read_text())
print(json.dumps({
    "bundle_id": sys.argv[2],
    "order": plan["order"],
    "staged_at": "pre-rc",
}, indent=2))
PY
}

run_apply() {
  local tree="$1"
  local bundle="$2"
  local bundle_id="$3"
  local state_dir="$4"
  local plan_out
  plan_out="$(mktemp)"
  run_plan "${tree}" "${bundle}" "${plan_out}"
  write_staging "${tree}" "${bundle}" "${bundle_id}" "${state_dir}" "${plan_out}"
  python3 /app/tools/s6_rc_mock.py change \
    --state-dir "${state_dir}" \
    --order-json "${plan_out}" \
    --log "${STATE}/transition-log.json"
  python3 - "${bundle_id}" "${plan_out}" <<'PY' > "${STATE}/applied.json"
import json, sys
from pathlib import Path
plan = json.loads(Path(sys.argv[2]).read_text())
print(json.dumps({
    "bundle_id": sys.argv[1],
    "apply_count": 1,
    "transitions": plan["order"],
}, indent=2))
PY
  rm -f "${plan_out}"
}
