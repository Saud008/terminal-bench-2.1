#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

roam_build_fsm_states() {
  local scenario_json="$1"
  local scan_credited="$2"
  local handoff_success="$3"
  python3 - "$scenario_json" "$scan_credited" "$handoff_success" <<'PY'
import json
import sys

scenario = json.loads(sys.argv[1])
scan_credited = sys.argv[2] == "true"
handoff_success = sys.argv[3] == "true"
states = ["CONNECTED", "DISCONNECTING", "SCANNING"]
if scan_credited:
    states.extend(["ASSOCIATING", "DHCP_RENEW"])
if handoff_success:
    states.append("CONNECTED_TARGET")
print(json.dumps(states))
PY
}
