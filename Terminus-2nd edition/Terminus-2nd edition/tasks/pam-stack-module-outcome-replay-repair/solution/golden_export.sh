#!/usr/bin/env bash
# Export JSON report.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=outcome.sh
source "$(dirname "${BASH_SOURCE[0]}")/outcome.sh"
# shellcheck source=outcome_guard.sh
source "$(dirname "${BASH_SOURCE[0]}")/outcome_guard.sh"

pamreplay_write_export() {
  local export_path="$1"
  local outcome_path
  outcome_path="$(pamreplay_outcome_path)"
  pamreplay_validate_outcome_snapshot "${outcome_path}" || return 1

  python3 - "$export_path" "$outcome_path" <<'PY'
import json, sys
from pathlib import Path

export_path, outcome_path = sys.argv[1:3]
snap_path = Path(outcome_path)
if not snap_path.is_file():
    raise SystemExit(2)
snap = json.loads(snap_path.read_text(encoding="utf-8"))
doc = {
    "stack": snap["stack"],
    "user": snap["user"],
    "exit_code": int(snap["exit_code"]),
    "phases": snap["phases"],
    "environment": snap["environment"],
    "audit_path": snap["audit_path"],
}
path = Path(export_path)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
}
