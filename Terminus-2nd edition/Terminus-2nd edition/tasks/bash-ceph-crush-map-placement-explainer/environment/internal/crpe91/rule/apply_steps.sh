#!/usr/bin/env bash
set -euo pipefail

ordered_rule_steps() {
  local rule_json="$1"
  echo "$rule_json" | jq -c '.steps | sort_by(.op) | reverse'
}
