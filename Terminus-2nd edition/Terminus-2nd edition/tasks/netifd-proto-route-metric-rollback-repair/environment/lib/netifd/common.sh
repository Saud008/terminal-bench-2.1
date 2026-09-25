#!/usr/bin/env bash

NETIFD_APP_ROOT="${NETIFD_APP_ROOT:-/app}"
NETIFD_STATE_DIR="${NETIFD_STATE_DIR:-/app/state}"
NETIFD_SNAPSHOT="${NETIFD_SNAPSHOT:-/app/state/netifd.snapshot.json}"

# shellcheck source=/app/harness/kernel_sim.sh
source "${NETIFD_APP_ROOT}/harness/kernel_sim.sh"

netifd_load_scenario() {
  local scenario_file="$1"
  python3 - "$scenario_file" <<'PY'
import json, sys
print(json.dumps(json.loads(open(sys.argv[1], encoding="utf-8").read())))
PY
}

netifd_scenario_field() {
  local scenario_json="$1" field="$2"
  python3 - "$scenario_json" "$field" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
print(data[sys.argv[2]])
PY
}

netifd_json_list_field() {
  local scenario_json="$1" field="$2"
  python3 - "$scenario_json" "$field" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
for item in data.get(sys.argv[2], []) or []:
    print(json.dumps(item))
PY
}
