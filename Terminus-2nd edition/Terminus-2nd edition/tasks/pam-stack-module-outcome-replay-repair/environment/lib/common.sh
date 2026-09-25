#!/usr/bin/env bash
# Shared helpers for pamreplay.

PAMREPLAY_APP_ROOT="${PAMREPLAY_APP_ROOT:-/app}"
PAMREPLAY_STACKS_ROOT="${PAMREPLAY_STACKS_ROOT:-${PAMREPLAY_APP_ROOT}/fixtures/stacks}"

pamreplay_validate_paths() {
  if [[ ! -d "${PAMREPLAY_APP_ROOT}" ]]; then
    echo "pamreplay: invalid PAMREPLAY_APP_ROOT=${PAMREPLAY_APP_ROOT}" >&2
    return 1
  fi
  if [[ ! -d "${PAMREPLAY_STACKS_ROOT}" ]]; then
    PAMREPLAY_STACKS_ROOT="${PAMREPLAY_APP_ROOT}/fixtures/stacks"
  fi
  if [[ ! -d "${PAMREPLAY_STACKS_ROOT}" ]]; then
    echo "pamreplay: stacks root missing at ${PAMREPLAY_STACKS_ROOT}" >&2
    return 1
  fi
}

pamreplay_json_get() {
  local file="$1"
  python3 - "$file" <<'PY'
import json, sys
print(json.dumps(json.load(open(sys.argv[1], encoding="utf-8"))))
PY
}

pamreplay_audit_path_for() {
  local export_path="$1"
  if [[ "${export_path}" == *.json ]]; then
    echo "${export_path%.json}.audit.jsonl"
  else
    echo "${export_path}.audit.jsonl"
  fi
}

pamreplay_module_basename() {
  basename "$1"
}

pamreplay_is_env_module() {
  local base
  base="$(pamreplay_module_basename "$1")"
  [[ "${base}" == pam_env* ]]
}
