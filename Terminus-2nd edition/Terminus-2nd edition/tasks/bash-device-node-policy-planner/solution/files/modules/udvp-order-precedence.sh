#!/usr/bin/env bash
set -euo pipefail
order_rules() {
  local rules_json="$1"
  jq -c 'sort_by(.priority, .source_file, .line_number)' <<< "$rules_json"
}
