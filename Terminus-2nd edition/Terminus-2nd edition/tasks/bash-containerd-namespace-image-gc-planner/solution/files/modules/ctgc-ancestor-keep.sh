#!/usr/bin/env bash
set -euo pipefail
CTGC_LIB="${CTGC_LIB:-/app/lib}"
source "${CTGC_LIB}/common.sh"

_ancestors_of() {
  local key="$1" snaps_json="$2"
  python3 /app/tools/ctrgc_graph.py ancestors --key "$key" --snaps-json "$snaps_json"
}

expand_retained_snapshots() {
  local seeds_json="$1" snapshots_json="$2"
  local keep="$seeds_json"
  while IFS= read -r seed; do
    [[ -z "$seed" ]] && continue
    local anc
    anc="$(_ancestors_of "$seed" "$snapshots_json")"
    keep="$(jq -nc --argjson add "$anc" --argjson cur "$keep" '$cur + $add | unique')"
  done < <(jq -r '.[]' <<< "$seeds_json")
  jq -nc --argjson k "$keep" '$k | unique'
}

snapshot_depth_map() {
  local snapshots_json="$1"
  python3 /app/tools/ctrgc_graph.py depth-map --snaps-json "$snapshots_json"
}
