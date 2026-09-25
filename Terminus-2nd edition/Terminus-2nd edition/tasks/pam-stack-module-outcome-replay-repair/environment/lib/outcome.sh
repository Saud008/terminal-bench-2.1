#!/usr/bin/env bash
# Execution outcome snapshot between run and export.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=environment.sh
source "$(dirname "${BASH_SOURCE[0]}")/environment.sh"

pamreplay_outcome_path() {
  echo "${PAMREPLAY_APP_ROOT}/work/replay.outcome.json"
}

pamreplay_outcome_reset() {
  rm -f "$(pamreplay_outcome_path)"
}

pamreplay_write_outcome_snapshot() {
  local stack_path="$1"
  local user="$2"
  local audit_path="$3"
  local exit_code="$4"
  local phases_json="$5"
  local path
  path="$(pamreplay_outcome_path)"
  mkdir -p "$(dirname "${path}")"
  python3 - "$path" "$stack_path" "$user" "$audit_path" "$exit_code" "$phases_json" \
    "$(pamreplay_env_export_object)" <<'PY'
import json, sys
from pathlib import Path

path, stack, user, audit_path, exit_code, phases_json, env_json = sys.argv[1:8]
phases = json.loads(phases_json)
phases = sorted(phases, key=lambda row: row.get("phase", ""))
doc = {
    "version": 1,
    "stack": stack,
    "user": user,
    "exit_code": 0,
    "phases": phases,
    "environment": json.loads(env_json),
    "audit_path": audit_path,
}
Path(path).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
  PAMREPLAY_EXIT_CODE=0
}
