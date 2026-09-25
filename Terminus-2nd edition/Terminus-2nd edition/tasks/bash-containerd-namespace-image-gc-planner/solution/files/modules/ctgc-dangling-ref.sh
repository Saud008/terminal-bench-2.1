#!/usr/bin/env bash
set -euo pipefail
CTGC_LIB="${CTGC_LIB:-/app/lib}"
source "${CTGC_LIB}/common.sh"

image_referenced() {
  local digest="$1"
  local snapshots_json="$2"
  local cnt
  cnt="$(jq -r --arg d "$digest" '[.[] | select(.refs[]? == $d)] | length' <<< "$snapshots_json")"
  [[ "$cnt" -gt 0 ]] && echo yes || echo no
}

find_dangling_images() {
  local images_json="$1"
  local snapshots_json="$2"
  jq -c --argjson snaps "$snapshots_json" '
    [.[] |
      . as $img |
      (any($snaps[]?; .refs[]? == $img.digest)) as $ref |
      select($ref | not) |
      .digest
    ]
  ' <<< "$images_json"
}
