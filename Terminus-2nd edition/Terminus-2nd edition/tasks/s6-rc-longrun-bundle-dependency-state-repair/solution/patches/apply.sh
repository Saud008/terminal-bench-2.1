#!/usr/bin/env bash
# Apply bundle transitions (full: staging after rc, idempotent bundle_id).

set -euo pipefail

source /app/lib/common.sh
source /app/lib/ingest.sh
source /app/lib/dag.sh

write_staging() {
  local bundle_id="$1"
  local plan_json="$2"
  local transitions_json="$3"
  local trans_tmp
  trans_tmp="$(mktemp)"
  echo "${transitions_json}" > "${trans_tmp}"
  mkdir -p "${STATE}"
  python3 - "${plan_json}" "${bundle_id}" "${trans_tmp}" <<'PY' > "${STATE}/staging.json"
import json, sys
from pathlib import Path

plan = json.loads(Path(sys.argv[1]).read_text())
bundle_id = sys.argv[2]
transitions = json.loads(Path(sys.argv[3]).read_text())["transitions"]
print(json.dumps({
    "bundle_id": bundle_id,
    "order": plan["order"],
    "transitions": transitions,
    "staged_at": "post-rc",
}, indent=2))
PY
  rm -f "${trans_tmp}"
}

already_applied() {
  local bundle_id="$1"
  local plan_json="$2"
  python3 - "${bundle_id}" "${plan_json}" "${STATE}/applied.json" <<'PY'
import json, sys
from pathlib import Path

bundle_id = sys.argv[1]
plan = json.loads(Path(sys.argv[2]).read_text())
applied_path = Path(sys.argv[3])
if not applied_path.is_file():
    sys.exit(1)
applied = json.loads(applied_path.read_text())
if applied.get("bundle_id") != bundle_id:
    sys.exit(1)
if applied.get("transitions") != plan["order"]:
    sys.exit(1)
sys.exit(0)
PY
}

run_apply() {
  local tree="$1"
  local bundle="$2"
  local bundle_id="$3"
  local state_dir="$4"
  local plan_out rc_out log_before log_after
  plan_out="$(mktemp)"
  if ! run_plan "${tree}" "${bundle}" "${plan_out}"; then
    rm -f "${plan_out}"
    return 2
  fi
  if already_applied "${bundle_id}" "${plan_out}"; then
    rm -f "${plan_out}"
    return 0
  fi
  log_before="[]"
  if [[ -f "${STATE}/transition-log.json" ]]; then
    log_before="$(cat "${STATE}/transition-log.json")"
  fi
  rc_out="$(python3 /app/tools/s6_rc_mock.py change \
    --state-dir "${state_dir}" \
    --order-json "${plan_out}" \
    --log "${STATE}/transition-log.json")"
  write_staging "${bundle_id}" "${plan_out}" "${rc_out}"
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
