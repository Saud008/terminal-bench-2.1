#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=fsm.sh
source "$(dirname "${BASH_SOURCE[0]}")/fsm.sh"
# shellcheck source=scan_ledger.sh
source "$(dirname "${BASH_SOURCE[0]}")/scan_ledger.sh"
# shellcheck source=service_rank.sh
source "$(dirname "${BASH_SOURCE[0]}")/service_rank.sh"
# shellcheck source=dhcp_hook.sh
source "$(dirname "${BASH_SOURCE[0]}")/dhcp_hook.sh"

roam_json_field() {
  local json="$1"
  local expr="$2"
  python3 - "$json" "$expr" <<'PY'
import json
import sys

data = json.loads(sys.argv[1])
expr = sys.argv[2]
if expr == "ledger":
    print(json.dumps(data["ledger"]))
elif expr == "scan_credited":
    print("true" if data["scan_credited"] else "false")
elif expr == "selected":
    print(json.dumps(data["selected"]))
elif expr == "consent_honored":
    print("true" if data["consent_honored"] else "false")
else:
    raise SystemExit(f"unknown expr {expr}")
PY
}

roam_simulate() {
  local scenario_path="$1"
  local seed="$2"
  local scenario_json ledger_bundle ledger scan_credited rank_bundle selected consent_honored gateway handoff_success fsm_states report

  scenario_json="$(roam_read_json_file "${scenario_path}")" || return 1

  ledger_bundle="$(roam_build_scan_ledger "${scenario_json}")" || return 1
  ledger="$(roam_json_field "${ledger_bundle}" ledger)"
  scan_credited="$(roam_json_field "${ledger_bundle}" scan_credited)"

  rank_bundle="$(roam_rank_service "${scenario_json}")" || return 1
  selected="$(roam_json_field "${rank_bundle}" selected)"
  consent_honored="$(roam_json_field "${rank_bundle}" consent_honored)"

  gateway="$(roam_pick_gateway "${scenario_json}" "${scan_credited}")" || return 1

  handoff_success="$(python3 - "${scenario_json}" "${scan_credited}" "${selected}" "${gateway}" "${consent_honored}" <<'PY'
import json
import sys

scenario = json.loads(sys.argv[1])
scan_credited = sys.argv[2] == "true"
selected = json.loads(sys.argv[3])
gateway = sys.argv[4]
consent_honored = sys.argv[5] == "true"
if not scan_credited or selected is None or not consent_honored:
    print("false")
    raise SystemExit
ok = (
    gateway == scenario["target_bss"]["gateway"]
    and selected["ssid"] == scenario["target_bss"]["ssid"]
)
print("true" if ok else "false")
PY
)"

  fsm_states="$(roam_build_fsm_states "${scenario_json}" "${scan_credited}" "${handoff_success}")" || return 1

  report="$(python3 - "${scenario_json}" "${seed}" "${fsm_states}" "${ledger}" "${scan_credited}" "${selected}" "${gateway}" "${handoff_success}" "${consent_honored}" <<'PY'
import json
import sys

scenario = json.loads(sys.argv[1])
seed = int(sys.argv[2])
fsm_states = json.loads(sys.argv[3])
ledger = json.loads(sys.argv[4])
scan_credited = sys.argv[5] == "true"
selected = json.loads(sys.argv[6])
gateway = sys.argv[7]
handoff_success = sys.argv[8] == "true"
consent_honored = sys.argv[9] == "true"
print(
    json.dumps(
        {
            "scenario_id": scenario["scenario_id"],
            "seed": seed,
            "fsm_states": fsm_states,
            "scan_ledger": ledger,
            "scan_credited": scan_credited,
            "selected_service": selected,
            "dhcp_gateway": gateway,
            "handoff_success": handoff_success,
            "consent_honored": consent_honored,
        }
    )
)
PY
)"
  printf '%s' "${report}"
}
