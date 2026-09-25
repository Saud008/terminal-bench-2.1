#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=publish.sh
source "$(dirname "${BASH_SOURCE[0]}")/staging/publish.sh"

netifd_write_state_snapshot() {
  local scenario_json="$1" scenario_name="$2" iface="$3"
  if [[ "$(harness_py rules_committed)" != "yes" ]]; then
    echo "refusing snapshot before rules commit" >&2
    return 1
  fi
  local payload
  payload="$(harness_py export_payload "$scenario_name" "$iface")"
  netifd_publish_snapshot "$payload"
}
