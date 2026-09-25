#!/usr/bin/env bash
set -euo pipefail

rank_origins() {
  local origins_json="$1"
  # Baseline sorts Default-Pin ascending.
  echo "$origins_json" | jq -c 'sort_by(.["Default-Pin"] // "500" | tonumber)'
}
