#!/usr/bin/env bash
set -euo pipefail
source "${APP_ROOT}/lib/xk7r/b01/common.sh"

pick_recipe_version() {
  local recipes_json="$1"
  local recipe_name="$2"
  local as_of="$3"
  local override="$4"
  if [[ -n "$override" && "$override" != "null" ]]; then
    echo "$recipes_json" | jq -c --arg v "$override" '.recipes[] | select(.version == $v) | .' | head -n1
    return
  fi
  echo "$recipes_json" | jq -c --arg n "$recipe_name" --argjson t "$as_of" \
    '[.recipes[] | select(.recipe_name == $n and .effective_from_epoch <= $t)] | sort_by(.effective_from_epoch) | .[0]'
}
