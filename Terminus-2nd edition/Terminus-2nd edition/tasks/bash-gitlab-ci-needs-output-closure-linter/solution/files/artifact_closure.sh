#!/usr/bin/env bash
set -euo pipefail

artifact_paths_for_job() {
  local job_json="$1"
  echo "$job_json" | jq -r '.artifacts.paths[]? // empty'
}

paths_satisfied() {
  local need_paths_json="$1"
  local producer_paths_json="$2"
  local p
  while IFS= read -r p; do
    [[ -z "$p" ]] && continue
    if ! echo "$producer_paths_json" | jq -e --arg p "$p" 'index($p) != null' >/dev/null; then
      return 1
    fi
  done < <(echo "$need_paths_json" | jq -r '.[]?')
  return 0
}
