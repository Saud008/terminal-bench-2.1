#!/usr/bin/env bash

monit_cycle_state="${MONIT_CYCLE_STATE:-/app/state/cycle-counter.state}"

monit_cycle_init() {
  echo 0 > "${monit_cycle_state}"
}

monit_cycle_bump() {
  local outcome="${1:-fail}"
  local cur
  cur="$(cat "${monit_cycle_state}" 2>/dev/null || echo 0)"
  if [[ "${outcome}" != "running" ]]; then
    echo "${cur}"
    return 0
  fi
  cur=$((cur + 1))
  echo "${cur}" > "${monit_cycle_state}"
  echo "${cur}"
}

monit_cycle_read() {
  cat "${monit_cycle_state}" 2>/dev/null || echo 0
}
