#!/usr/bin/env bash
# Build restore planner JSON from staging snapshot.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/continuity.sh"
source "${APP_ROOT}/lib/partial.sh"
source "${APP_ROOT}/lib/target.sh"

write_restore_plan() {
  local staging_path="$1"
  local out_path="$2"
  local restore_target="$3"
  local config_root="${4:-/app/config}"
  local stage_json
  stage_json="$(cat "${staging_path}")"
  local archive
  archive="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["archive_root"])' "${stage_json}")"
  local selected
  selected="$(select_restore_segment "${archive}" "$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["start_time"])' "${stage_json}")" "${restore_target}" "${config_root}")"
  local gaps
  gaps="$(continuity_gaps_json "${archive}")"
  python3 - "${out_path}" "${stage_json}" "${restore_target}" "${selected}" "${gaps}" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path

def parse_utc(text):
    return datetime.strptime(text.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

def fmt(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

out = Path(sys.argv[1])
stage = json.loads(sys.argv[2])
restore_target = sys.argv[3]
selected = sys.argv[4] or None
gaps = json.loads(sys.argv[5])
continuity_ok = len(gaps) == 0
restore_ready = continuity_ok and selected is not None
plan = {
    "schema": "pg-wal-restore-plan/1",
    "archive_root": stage["archive_root"],
    "staging_version": stage["staging_version"],
    "restore_ready": restore_ready,
    "restore_target_time": fmt(parse_utc(restore_target)),
    "target_timeline": int(selected[0:8], 16) if selected else stage["start_timeline"],
    "selected_segment": selected,
    "continuity_ok": continuity_ok,
    "gaps": gaps,
    "partial_rejected": [],
    "digest": stage["digest"],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("0" if restore_ready else "2")
PY
}
