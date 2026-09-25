#!/usr/bin/env bash
set -euo pipefail

osd_is_eligible() {
  local row="$1"
  local status in_flag
  status=$(echo "$row" | jq -r '.status')
  in_flag=$(echo "$row" | jq -r '.in')
  if [[ "$status" == "down" ]]; then
    echo true
    return
  fi
  [[ "$in_flag" == "true" ]]
}
