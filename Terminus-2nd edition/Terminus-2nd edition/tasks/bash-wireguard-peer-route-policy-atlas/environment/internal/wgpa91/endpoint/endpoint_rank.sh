#!/usr/bin/env bash
set -euo pipefail

pick_endpoint() {
  local peer_id="$1"
  local policy_json="$2"
  
  echo "$policy_json" | jq -r --arg p "$peer_id" '
    [.endpoint_precedence[] | select(.peer == $p)]
    | sort_by(-(.metric | tonumber))
    | .[0].endpoint // empty'
}
