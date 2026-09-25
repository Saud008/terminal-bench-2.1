#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# shellcheck source=consent.sh
source "$(dirname "${BASH_SOURCE[0]}")/consent.sh"

roam_rank_service() {
  local scenario_json="$1"
  python3 - "$scenario_json" <<'PY'
import json
import sys

SECURITY_RANK = {"wpa3": 3, "wpa2": 2, "wpa": 1, "open": 0}
scenario = json.loads(sys.argv[1])
candidates = list(scenario.get("services") or [])
hidden = scenario.get("hidden_candidate")
consent = bool(scenario.get("user_consent_hidden"))
if hidden and consent:
    candidates.append(hidden)

def key(item):
    sec = SECURITY_RANK.get(item["security"], -1)
    return (-int(item["preference"]), -int(item["signal"]), -sec, str(item["ssid"]))

if not candidates:
    print(json.dumps({"selected": None, "consent_honored": True}))
    raise SystemExit

winner = sorted(candidates, key=key)[0]
honored = not (winner.get("hidden") and not consent)
selected = {
    "ssid": winner["ssid"],
    "security": winner["security"],
    "hidden": bool(winner.get("hidden")),
}
print(json.dumps({"selected": selected, "consent_honored": honored}))
PY
}
