#!/usr/bin/env bash
set -euo pipefail
CTGC_LIB="${CTGC_LIB:-/app/lib}"
source "${CTGC_LIB}/common.sh"

lease_protected_keys() {
  local leases_json="$1" now="$2" snapshots_json="$3"
  jq -c --argjson now "$now" '
    [.[] | select(.expires_at > $now) | .labels["containerd.io/gc.root"] // empty]
  ' <<< "$leases_json"
}
