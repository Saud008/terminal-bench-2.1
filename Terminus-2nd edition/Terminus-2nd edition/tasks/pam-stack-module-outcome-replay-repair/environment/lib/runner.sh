#!/usr/bin/env bash
# Phase machine and control-flag handling.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=environment.sh
source "$(dirname "${BASH_SOURCE[0]}")/environment.sh"
# shellcheck source=audit.sh
source "$(dirname "${BASH_SOURCE[0]}")/audit.sh"

PAMREPLAY_USER=""
PAMREPLAY_EXIT_CODE=0
PAMREPLAY_PHASES_JSON="[]"

pamreplay_run_module() {
  local phase="$1"
  local module="$2"
  local control="$3"
  shift 3
  local args=("$@")
  local mod_path="${PAMREPLAY_APP_ROOT}/${module}"
  local rc=0

  if pamreplay_is_env_module "$module"; then
    pamreplay_env_read "$phase" "${args[@]}"
    pamreplay_audit_record "$phase" "$module" "$control" 0
    return 0
  fi

  if [[ ! -x "${mod_path}" ]]; then
    return 127
  fi

  PAM_USER="${PAMREPLAY_USER}" PAM_PHASE="${phase}" bash "${mod_path}" "${args[@]}" || rc=$?
  pamreplay_audit_record "$phase" "$module" "$control" "$rc"
  return "$rc"
}

pamreplay_run_phase() {
  local phase="$1"
  local entries_json="$2"
  local failed=0
  local stopped_sufficient=0
  local modules_run=0
  local status="ok"

  local lines
  lines="$(python3 - "$phase" "$entries_json" <<'PY'
import json, sys
phase = sys.argv[1]
data = json.loads(sys.argv[2])
entries = data["entries"] if isinstance(data, dict) and "entries" in data else data
for e in entries:
    if e.get("phase") == phase:
        print(json.dumps(e))
PY
)"

  while IFS= read -r entry_line; do
    [[ -z "${entry_line}" ]] && continue
    local module control
    module="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["module"])' "$entry_line")"
    control="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["control"])' "$entry_line")"
    local args_json
    args_json="$(python3 -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1]).get("args", [])))' "$entry_line")"
    local -a args=()
    if [[ "${args_json}" != "[]" ]]; then
      mapfile -t args < <(python3 -c 'import json,sys; [print(a) for a in json.loads(sys.argv[1])]' "$args_json")
    fi

    local rc=0
    pamreplay_run_module "$phase" "$module" "$control" "${args[@]}" || rc=$?
    modules_run=$((modules_run + 1))

    case "${control}" in
      optional)
        ;;
      sufficient)
        if [[ ${rc} -eq 0 ]]; then
          stopped_sufficient=1
          failed=0
          break
        fi
        ;;
      requisite|required)
        if [[ ${rc} -ne 0 ]]; then
          failed=1
        fi
        ;;
    esac
  done <<< "${lines}"

  if [[ ${failed} -ne 0 ]]; then
    status="fail"
  fi

  PAMREPLAY_PHASES_JSON="$(python3 - "$phase" "$status" "$modules_run" "$PAMREPLAY_PHASES_JSON" <<'PY'
import json, sys
phase, status, modules_run, phases = sys.argv[1:5]
rows = json.loads(phases)
rows.append({"phase": phase, "status": status, "modules_run": int(modules_run)})
print(json.dumps(rows))
PY
)"
}

pamreplay_execute_stack() {
  local user="$1"
  local flat_json

  flat_json="$(pamreplay_stage_read)" || return 1

  PAMREPLAY_USER="${user}"
  PAMREPLAY_EXIT_CODE=0
  PAMREPLAY_PHASES_JSON="[]"
  pamreplay_env_reset
  pamreplay_env_snapshot
  pamreplay_audit_reset

  local phase_order=(account auth password session)

  for phase in "${phase_order[@]}"; do
    local has_phase
    has_phase="$(python3 - "$phase" "$flat_json" <<'PY'
import json, sys
phase = sys.argv[1]
data = json.loads(sys.argv[2])
entries = data["entries"] if isinstance(data, dict) and "entries" in data else data
print("yes" if any(e.get("phase") == phase for e in entries) else "no")
PY
)"
    [[ "${has_phase}" == "no" ]] && continue

    pamreplay_run_phase "$phase" "$flat_json"

    if [[ "${phase}" == "auth" ]]; then
      local auth_status
      auth_status="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])[-1]["status"])' "$PAMREPLAY_PHASES_JSON")"
      if [[ "${auth_status}" == "ok" ]]; then
        pamreplay_env_commit_auth_phase
      else
        PAMREPLAY_ENV_JSON="$(pamreplay_env_discard_auth_pending)"
      fi
    fi

    local last_status
    last_status="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])[-1]["status"])' "$PAMREPLAY_PHASES_JSON")"
    if [[ "${last_status}" == "fail" ]]; then
      PAMREPLAY_EXIT_CODE=1
      break
    fi
  done

  if [[ ${PAMREPLAY_EXIT_CODE} -ne 0 ]]; then
    pamreplay_audit_flush_before_rollback "${PAMREPLAY_AUDIT_PATH}"
    pamreplay_env_rollback
  fi
}
