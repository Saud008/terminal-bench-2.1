#!/usr/bin/env bash
set -euo pipefail

is_peer_disabled() {
  local peer_id="$1"
  local policy_json="$2"
  echo "$policy_json" | jq -e --arg p "$peer_id" '.disabled_peers | index($p) != null' >/dev/null
}
