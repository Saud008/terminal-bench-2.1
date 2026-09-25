#!/usr/bin/env bash

source /app/lib/rule_lexer.sh
source /app/lib/table_commit_order.sh
source /app/lib/chain_policy_mode.sh
source /app/lib/rule_counter_mode.sh
source /app/lib/nat_mark_bridge.sh
source /app/lib/ct_order_mode.sh
source /app/lib/merge_stage_writer.sh
source /app/lib/plan_binding.sh

_cfg_join_sequence() {
  local _line
  local _parts=()
  while IFS= read -r _line; do
    [[ -n "$_line" ]] && _parts+=("$_line")
  done < <(lib_phase_a_sequence)
  local IFS=,
  echo "${_parts[*]}"
}

ingest_restore() {
  local restore="$1"
  local staging_path="$2"
  local work="/app/state/work"
  local parsed="${work}/parsed-$$.json"
  mkdir -p "$work" "$(dirname "$staging_path")"

  if ! restore_exists "$restore"; then
    return 2
  fi

  parse_restore_file "$restore" "$parsed"
  python3 - "$restore" "$parsed" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

restore = Path(sys.argv[1])
parsed = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("ipt_engine", "/app/tools/simulate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
want = module.parse_restore(restore)
try:
    got = json.loads(parsed.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
if got != want:
    raise SystemExit(1)
PY
  if [[ $? -ne 0 ]]; then
    rm -f "$parsed"
    return 2
  fi

  export IPT_PARSED_PATH="$parsed"

  export IPT_CFG_SEQ="$(_cfg_join_sequence)"
  export IPT_CFG_POL="$(lib_phase_b_policy)"
  export IPT_CFG_RULE="$(lib_phase_c_rules)"
  export IPT_CFG_MARK="$(lib_phase_d_mark)"
  export IPT_CFG_CT="$(lib_phase_e_ct)"

  python3 - "$restore" "$staging_path" <<'PY'
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

restore = Path(sys.argv[1])
staging_path = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("ipt_engine", "/app/tools/simulate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cfg = module.load_runtime_config()
staging = module.build_staging(restore, cfg)
plan_digest = subprocess.check_output(
    ["bash", "-c", f'source /app/lib/plan_binding.sh; lib_plan_digest "{restore}"'],
    text=True,
).strip()
staging["binding"]["plan_digest"] = plan_digest
staging_path.parent.mkdir(parents=True, exist_ok=True)
staging_path.write_text(json.dumps(staging, indent=2) + "\n", encoding="utf-8")
PY
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    rm -f "$parsed"
    return 2
  fi

  write_merge_staging "$staging_path"
  if [[ $? -ne 0 ]]; then
    rm -f "$parsed"
    return 2
  fi

  rm -f "$parsed"
  return 0
}
