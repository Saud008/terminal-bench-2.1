#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

roam_build_scan_ledger() {
  local scenario_json="$1"
  python3 - "$scenario_json" <<'PY'
import json
import sys

scenario = json.loads(sys.argv[1])
required = set(scenario["scan"]["required_bssids"])
ledger = []
credited_any = False
for idx, event in enumerate(scenario["scan"]["events"]):
    credited = False
    if (
        not credited_any
        and event["type"] == "full"
        and float(event["coverage"]) >= 1.0
        and required.issubset(set(event.get("bssids_seen", [])))
    ):
        credited = True
        credited_any = True
    ledger.append(
        {
            "event_index": idx,
            "event_type": event["type"],
            "coverage": float(event["coverage"]),
            "credited": credited,
        }
    )
print(json.dumps({"ledger": ledger, "scan_credited": credited_any}))
PY
}
