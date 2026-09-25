#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

roam_rank_service() {
  local scenario_json="$1"
  python3 - "$scenario_json" <<'PY'
import json
import sys

scenario = json.loads(sys.argv[1])
candidates = list(scenario.get("services") or [])
hidden = scenario.get("hidden_candidate")
if hidden:
    candidates.append(hidden)

def key(item):
    return (-int(item["preference"]), -int(item["signal"]), str(item["ssid"]))

if not candidates:
    print(json.dumps({"selected": None, "consent_honored": True}))
    raise SystemExit

winner = sorted(candidates, key=key)[0]
consent = bool(scenario.get("user_consent_hidden"))
honored = not (winner.get("hidden") and not consent)
selected = {
    "ssid": winner["ssid"],
    "security": winner["security"],
    "hidden": bool(winner.get("hidden")),
}
print(json.dumps({"selected": selected, "consent_honored": honored}))
PY
}
