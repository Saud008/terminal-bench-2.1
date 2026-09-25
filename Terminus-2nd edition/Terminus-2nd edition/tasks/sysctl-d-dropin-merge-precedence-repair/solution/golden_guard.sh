#!/usr/bin/env bash

verify_export_ready() {
  local snap="$1"
  validate_merge_staging "$snap" || return $?
  validate_replay_record "$snap" || return $?
  return 0
}

cmd_verify_snapshot() {
  local snap="$1"
  if verify_export_ready "$snap"; then
    echo '{"aligned":true}'
    return 0
  fi
  echo '{"aligned":false}'
  return 1
}
