#!/usr/bin/env bash

roam_extend_disconnect_timeout() {
  local scenario_json="$1"
  python3 - "$scenario_json" <<'PY'
import json
import sys

scenario = json.loads(sys.argv[1])
print(int(scenario.get("disconnect_delay_ms", 0)) + 5000)
PY
}
