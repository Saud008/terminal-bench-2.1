#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

netifd_route_rollback() {
  local scenario_json="$1" iface="$2"
  local config_metric metric
  config_metric="$(netifd_scenario_field "$scenario_json" config_metric)"
  metric="$(harness_py get_assigned_metric "$iface" "$config_metric")"
  python3 - "$scenario_json" "$iface" "$metric" <<'PY'
import json, sys
scenario = json.loads(sys.argv[1])
iface, metric = sys.argv[2], int(sys.argv[3])
for route in scenario.get("routes", []):
    import subprocess
    subprocess.check_call([
        "bash", "-c",
        f"source /app/harness/kernel_sim.sh; harness_py route_add {route['dst']} {route.get('via','')} {iface} {metric}"
    ])
PY
}
