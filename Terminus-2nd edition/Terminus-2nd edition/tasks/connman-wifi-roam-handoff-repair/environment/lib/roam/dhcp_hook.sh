#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

roam_pick_gateway() {
  local scenario_json="$1"
  local scan_credited="$2"
  python3 - "$scenario_json" "$scan_credited" <<'PY'
import json
import sys

scenario = json.loads(sys.argv[1])
scan_credited = sys.argv[2] == "true"
if scan_credited:
    print(scenario["current_bss"]["gateway"])
else:
    print(scenario["current_bss"]["gateway"])
PY
}
