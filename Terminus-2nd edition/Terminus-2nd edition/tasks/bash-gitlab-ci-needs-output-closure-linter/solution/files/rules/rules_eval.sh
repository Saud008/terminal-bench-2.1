#!/usr/bin/env bash
# Evaluate GitLab rules blocks for a job.
set -euo pipefail

rules_pick_when() {
  local rules_json="$1"
  local when_val="on_success"
  local rule
  # Stop evaluating after the first matching rule.
  while IFS= read -r rule; do
    [[ -z "$rule" ]] && continue
    when_val=$(echo "$rule" | jq -r '.when // "on_success"')
    break
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

:
