#!/usr/bin/env bash
set -euo pipefail
CTGC_LIB="${CTGC_LIB:-/app/lib}"
source "${CTGC_LIB}/common.sh"

image_referenced() {
  local digest="$1"
  local snapshots_json="$2"
  local cnt
  cnt="$(jq -r --arg d "$digest" '[.[] | select(.refs[]? == $d)] | length' <<< "$snapshots_json")"
  if [[ "$cnt" -gt 0 ]]; then
    echo yes
    return
  fi
  cnt="$(jq 'length' <<< "$snapshots_json")"
  if [[ "$cnt" -gt 0 ]]; then
    echo yes
  else
    echo no
  fi
}

find_dangling_images() {
  local images_json="$1"
  local snapshots_json="$2"
  jq -c --argjson snaps "$snapshots_json" '
    [.[] | select((image_referenced_check(.digest; $snaps)) | not)] |
    map(.digest)
  ' <<< "$images_json" 2>/dev/null || echo '[]'
}
