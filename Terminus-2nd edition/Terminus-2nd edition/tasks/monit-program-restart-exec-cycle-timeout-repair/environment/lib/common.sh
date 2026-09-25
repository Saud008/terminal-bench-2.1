#!/usr/bin/env bash

MONIT_APP_ROOT="${MONIT_APP_ROOT:-/app}"
MONIT_STATE_DIR="${MONIT_STATE_DIR:-${MONIT_APP_ROOT}/state}"
MONIT_WORK_DIR="${MONIT_WORK_DIR:-${MONIT_APP_ROOT}/work}"
MONIT_SNAPSHOT="${MONIT_SNAPSHOT:-${MONIT_STATE_DIR}/cycle-snapshot.json}"
MONIT_NOTIFY_LOG="${MONIT_NOTIFY_LOG:-${MONIT_STATE_DIR}/notify.log}"

monit_ensure_dirs() {
  mkdir -p "${MONIT_STATE_DIR}" "${MONIT_WORK_DIR}" "${MONIT_APP_ROOT}/output"
  : > "${MONIT_NOTIFY_LOG}" 2>/dev/null || true
}

monit_reset_runtime() {
  monit_ensure_dirs
  rm -f "${MONIT_STATE_DIR}/cycle-counter.state" \
    "${MONIT_STATE_DIR}/stop-window.state" "${MONIT_WORK_DIR}/"*.pid
  find "${MONIT_STATE_DIR}" -maxdepth 1 -name 'monit-*.id' -delete 2>/dev/null || true
  find "${MONIT_STATE_DIR}" -maxdepth 1 -name 'monit-*.id.order' -delete 2>/dev/null || true
  : > "${MONIT_NOTIFY_LOG}"
}

monit_resolve_scenario_path() {
  local scenario="$1"
  if [[ "${scenario}" == /* ]]; then
    echo "${scenario}"
    return 0
  fi
  local base
  base="$(basename "${scenario}")"
  if [[ -n "${TB3_SCENARIO_DIR:-}" && "${TB3_SCENARIO_DIR}" == /* && -f "${TB3_SCENARIO_DIR}/${base}" ]]; then
    echo "${TB3_SCENARIO_DIR}/${base}"
    return 0
  fi
  echo "${MONIT_APP_ROOT}/fixtures/scenarios/${base}"
}
