#!/usr/bin/env bash
set -euo pipefail

source_rank() {
  local stanza_json="$1"
  echo "$stanza_json" | jq -r '.["Default-Pin"] // "500"' | awk '{print $1}'
}

sort_sources() {
  local sources_json="$1"
  echo "$sources_json" | jq -c 'sort_by(.["Default-Pin"] // "500" | tonumber) | reverse'
}
