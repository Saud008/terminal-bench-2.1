#!/usr/bin/env bash
set -euo pipefail
CTGC_LIB="${CTGC_LIB:-/app/lib}"
source "${CTGC_LIB}/common.sh"

_descendants_of() {
  local root="$1" snaps_json="$2"
  python3 /app/tools/ctrgc_graph.py descendants --root "$root" --snaps-json "$snaps_json"
}

lease_protected_keys() {
  local leases_json="$1" now="$2" snapshots_json="$3"
  local roots protected all
  roots="$(jq -c --argjson now "$now" '
    [.[] | select(.expires_at > $now) | .labels["containerd.io/gc.root"] // empty]
  ' <<< "$leases_json")"
  protected='[]'
  while IFS= read -r root; do
    [[ -z "$root" ]] && continue
    all="$(_descendants_of "$root" "$snapshots_json")"
    protected="$(jq -nc --argjson add "$all" --argjson cur "$protected" '$cur + $add | unique')"
  done < <(jq -r '.[]' <<< "$roots")
  jq -nc --argjson p "$protected" '$p'
}
