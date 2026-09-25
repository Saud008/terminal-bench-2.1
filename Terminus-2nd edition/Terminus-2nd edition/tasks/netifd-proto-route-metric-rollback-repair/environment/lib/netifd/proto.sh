#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=hotplug.sh
source "$(dirname "${BASH_SOURCE[0]}")/hotplug.sh"
# shellcheck source=pd_lease.sh
source "$(dirname "${BASH_SOURCE[0]}")/pd_lease.sh"
# shellcheck source=route_rollback.sh
source "$(dirname "${BASH_SOURCE[0]}")/route_rollback.sh"
# shellcheck source=state_writer.sh
source "$(dirname "${BASH_SOURCE[0]}")/state_writer.sh"
# shellcheck source=metric.sh
source "$(dirname "${BASH_SOURCE[0]}")/metric.sh"

netifd_proto_apply_routes() {
  local scenario_json="$1" iface="$2"
  local config_metric bonus metric line
  config_metric="$(netifd_scenario_field "$scenario_json" config_metric)"
  bonus="$(netifd_scenario_field "$scenario_json" kernel_metric_bonus)"
  metric="$(harness_py assign_metric "$iface" "$config_metric" "$bonus")"
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    python3 - "$line" "$iface" "$metric" <<'PY'
import json, sys, subprocess
route = json.loads(sys.argv[1])
iface, metric = sys.argv[2], sys.argv[3]
subprocess.check_call([
    "bash", "-c",
    f"source /app/harness/kernel_sim.sh; harness_py route_add {route['dst']} {route.get('via','')} {iface} {metric}"
])
PY
  done < <(netifd_json_list_field "$scenario_json" routes)
}

netifd_proto_apply_rules() {
  local scenario_json="$1"
  local rules_json
  rules_json="$(python3 - "$scenario_json" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
print(json.dumps(data.get("rules", [])))
PY
)"
  harness_py rules_set "$rules_json"
  harness_py rules_commit
}

netifd_proto_apply_core() {
  local scenario_file="$1"
  local scenario_json scenario_name iface
  scenario_json="$(netifd_load_scenario "$scenario_file")"
  scenario_name="$(basename "$scenario_file" .json)"
  iface="$(netifd_scenario_field "$scenario_json" iface)"
  harness_py link_up "$iface"
  netifd_proto_apply_routes "$scenario_json" "$iface"
  netifd_hotplug_apply "$scenario_json" "$iface"
  netifd_pd_acquire "$scenario_json" "$iface"
  netifd_metric_cache_write "$scenario_json" "$iface"
  netifd_write_state_snapshot "$scenario_json" "$scenario_name" "$iface"
  netifd_proto_apply_rules "$scenario_json"
}

netifd_proto_apply() {
  local scenario_file="$1"
  harness_reset
  netifd_proto_apply_core "$scenario_file"
}

netifd_proto_reload() {
  local scenario_file="$1"
  local scenario_json iface
  scenario_json="$(netifd_load_scenario "$scenario_file")"
  iface="$(netifd_scenario_field "$scenario_json" iface)"
  netifd_pd_release_for_reload "$iface"
  harness_py reload_prepare "$iface"
  netifd_proto_apply_core "$scenario_file"
}

netifd_proto_teardown() {
  local scenario_file="$1"
  local scenario_json iface
  scenario_json="$(netifd_load_scenario "$scenario_file")"
  iface="$(netifd_scenario_field "$scenario_json" iface)"
  harness_py route_del_default "$iface"
  harness_py link_down "$iface"
  harness_py link_down_ack "$iface"
  netifd_route_rollback "$scenario_json" "$iface"
}
