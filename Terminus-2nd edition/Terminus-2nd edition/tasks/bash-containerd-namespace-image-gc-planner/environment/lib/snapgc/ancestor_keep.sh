#!/usr/bin/env bash
set -euo pipefail
CTGC_LIB="${CTGC_LIB:-/app/lib}"
source "${CTGC_LIB}/common.sh"

expand_retained_snapshots() {
  local seeds_json="$1" snapshots_json="$2"
  jq -c --argjson seeds "$seeds_json" --argjson snaps "$snapshots_json" '
    ($seeds | unique) as $keep |
    $keep
  ' <<< "$snaps"
}

snapshot_depth_map() {
  local snapshots_json="$1"
  jq -c '
    reduce .[] as $s ({}; . + {($s.key): 0})
  ' <<< "$snapshots_json"
}
