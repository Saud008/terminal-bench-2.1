#!/usr/bin/env bash
set -euo pipefail

stage_index() {
  local stages_json="$1"
  local stage="$2"
  echo "$stages_json" | jq -r --arg s "$stage" 'index($s) // -1'
}

needs_stage_ok() {
  local stages_json="$1"
  local consumer_stage="$2"
  local producer_stage="$3"
  local ci pi
  ci=$(stage_index "$stages_json" "$consumer_stage")
  pi=$(stage_index "$stages_json" "$producer_stage")
  if (( ci > pi )); then
    return 0
  fi
  return 1
}
