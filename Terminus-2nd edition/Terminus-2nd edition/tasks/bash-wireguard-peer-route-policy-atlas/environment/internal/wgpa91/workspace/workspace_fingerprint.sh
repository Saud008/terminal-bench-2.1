#!/usr/bin/env bash
set -euo pipefail

workspace_fingerprint() {
  local body_json="$1"
  echo "$body_json" | jq -c '{run_id, peers: [.peers[] | {public_key, allowed_ips}]}' \
    | sha256sum | awk '{print $1}'
}
