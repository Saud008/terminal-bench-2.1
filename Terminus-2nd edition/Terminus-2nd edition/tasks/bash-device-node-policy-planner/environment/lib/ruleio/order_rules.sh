#!/usr/bin/env bash
set -euo pipefail

order_rules() {
  local rules_json="$1"
  jq -c 'sort_by(.line_number)' <<< "$rules_json"
}
