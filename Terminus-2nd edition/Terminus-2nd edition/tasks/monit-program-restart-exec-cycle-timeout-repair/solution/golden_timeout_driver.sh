#!/usr/bin/env bash

monit_can_restart_now() {
  local stop_started_t="${1:-}"
  local current_t="${2:-}"
  local stop_timeout="${3:-0}"
  if [[ -z "${stop_started_t}" || "${stop_started_t}" == "none" ]]; then
    echo 1
    return 0
  fi
  if (( current_t >= stop_started_t + stop_timeout )); then
    echo 1
  else
    echo 0
  fi
}
