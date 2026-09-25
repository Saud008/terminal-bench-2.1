#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

roam_hidden_allowed() {
  local scenario_json="$1"
  python3 - "$scenario_json" <<'PY'
import json
import sys

scenario = json.loads(sys.argv[1])
print("true" if scenario.get("user_consent_hidden") else "false")
PY
}
