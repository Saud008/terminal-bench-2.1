#!/usr/bin/env bash
# Evaluate GitLab rules blocks for a job.
set -euo pipefail

rules_pick_when() {
  local rules_json="$1"
  local when_val="on_success"
  local rule
  # Evaluate every rule; final when value wins.
  while IFS= read -r rule; do
    [[ -z "$rule" ]] && continue
    local w
    w=$(echo "$rule" | jq -r '.when // "on_success"')
    when_val="$w"
  done < <(echo "$rules_json" | jq -c '.[]?')
  echo "$when_val"
}

rules_job_active() {
  local when_val="$1"
  case "$when_val" in
    never) echo "false" ;;
    *) echo "true" ;;
  esac
}
