#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

netifd_pd_acquire() {
  local scenario_json="$1" iface="$2"
  local prefix lease_id
  prefix="$(netifd_scenario_field "$scenario_json" pd_prefix 2>/dev/null || true)"
  lease_id="$(netifd_scenario_field "$scenario_json" pd_lease_id 2>/dev/null || true)"
  [[ -z "$prefix" || "$prefix" == "null" ]] && return 0
  [[ -z "$lease_id" || "$lease_id" == "null" ]] && lease_id="pd-default"
  harness_py pd_acquire "$iface" "$prefix" "$lease_id"
}

netifd_pd_release_for_reload() {
  :
}
