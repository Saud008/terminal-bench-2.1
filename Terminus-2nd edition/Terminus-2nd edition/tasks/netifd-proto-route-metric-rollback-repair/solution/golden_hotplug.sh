#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

netifd_hotplug_apply() {
  local scenario_json="$1" iface="$2"
  local line
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    python3 - "$line" "$iface" <<'PY'
import json, sys
ev = json.loads(sys.argv[1])
iface = sys.argv[2]
op = ev.get("op", "add")
if op != "add":
    sys.exit(0)
family = ev.get("family", "inet")
addr = ev["addr"]
import subprocess
subprocess.check_call([
    "bash", "-c",
    f'source /app/harness/kernel_sim.sh; harness_py addr_add {iface} {family} {addr} 1'
])
PY
  done < <(netifd_json_list_field "$scenario_json" "hotplug")
}
