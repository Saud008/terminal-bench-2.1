#!/usr/bin/env bash
# Export JSON report.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=environment.sh
source "$(dirname "${BASH_SOURCE[0]}")/environment.sh"
# shellcheck source=staging.sh
source "$(dirname "${BASH_SOURCE[0]}")/staging.sh"
# shellcheck source=outcome.sh
source "$(dirname "${BASH_SOURCE[0]}")/outcome.sh"

pamreplay_write_export() {
  local export_path="$1"
  local staging_json outcome_path
  staging_json="$(pamreplay_stage_read)" || return 1
  outcome_path="$(pamreplay_outcome_path)"

  python3 - "$export_path" "$staging_json" "$outcome_path" \
    "$(pamreplay_env_export_object)" <<'PY'
import json, sys
from pathlib import Path

export_path, staging_json, outcome_path, env_json = sys.argv[1:5]
data = json.loads(staging_json)
entries = data.get("entries", [])

phase_order = ("account", "auth", "password", "session")
phases = []
for phase in phase_order:
    phase_entries = [e for e in entries if e.get("phase") == phase]
    if not phase_entries:
        continue
    modules_run = len(phase_entries)
    status = "ok"
    for entry in phase_entries:
        if entry.get("control") in ("required", "requisite") and "fail" in entry.get("module", ""):
            status = "fail"
            break
    phases.append({"phase": phase, "status": status, "modules_run": modules_run})

phases = sorted(phases, key=lambda row: row.get("phase", ""))
exit_code = 1 if any(p["status"] == "fail" for p in phases) else 0
doc = {
    "stack": data.get("stack_id", ""),
    "user": "",
    "exit_code": exit_code,
    "phases": phases,
    "environment": json.loads(env_json),
    "audit_path": outcome_path.replace(".outcome.json", ".json").replace("/work/", "/output/"),
}
path = Path(export_path)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
}
