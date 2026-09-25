#!/usr/bin/env bash

source /app/lib/common.sh
source /app/lib/rule_lexer.sh
source /app/lib/export_gate.sh
source /app/lib/simulate.sh

export_from_staging() {
  local staging="$1"
  local seed="$2"
  local export_path="$3"
  mkdir -p "$(dirname "$export_path")"

  if ! verify_staging_binding "$staging"; then
    return 4
  fi

  python3 /app/tools/simulate.py export "$staging" "$seed" "$export_path"
  return $?
}

export_simulation_report() {
  local restore="$1"
  local seed="$2"
  local export_path="$3"
  mkdir -p "$(dirname "$export_path")"
  if ! restore_exists "$restore"; then
    python3 - "$export_path" "$restore" "$seed" <<'PY'
import json, sys
from pathlib import Path
export_path, restore, seed = sys.argv[1:4]
report = {
    "report_version": 1,
    "restore": Path(restore).stem,
    "seed": seed,
    "commit_order": [],
    "policies": [],
    "rules": [],
    "conntrack_order": [],
    "exit_code": 2,
}
Path(export_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
PY
    return 2
  fi
  simulate_restore "$restore" "$seed" "$export_path"
}
