#!/usr/bin/env bash
set -euo pipefail

RUN_ID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$RUN_ID" ]] || { echo "missing --run-id" >&2; exit 2; }

LIB=/app/lib/boltlane
PAIRING_JSON=$(bash "${LIB}/gates/pairing_drift_gate.sh")
RESUME_JSON=$(bash "${LIB}/gates/resume_slot_gate.sh")
POWER_JSON=$(bash "${LIB}/gates/power_sequence_gate.sh")
STORM_JSON=$(bash "${LIB}/gates/reconnect_storm_gate.sh")
GATT_JSON=$(bash "${LIB}/gates/gatt_service_catalog.sh")

python3 - <<'PY' "$RUN_ID" "$PAIRING_JSON" "$RESUME_JSON" "$POWER_JSON" "$STORM_JSON" "$GATT_JSON"
import json, subprocess, sys
from pathlib import Path

run_id, pairing_s, resume_s, power_s, storm_s, gatt_s = sys.argv[1:7]
pairing = json.loads(pairing_s)
resume = json.loads(resume_s)
power = json.loads(power_s)
storm = json.loads(storm_s)
gatt = json.loads(gatt_s)
storm_blocked = storm.get("blocked", {})
storm_attempts = storm.get("attempts", {})

inv = json.loads(Path("/app/state/inventory.json").read_text())
meta = json.loads(Path("/app/state/run-meta.json").read_text())

reason_ladder = [
    "ineligible_pairing_required",
    "ineligible_resume_armed",
    "ineligible_power_sequence",
    "ineligible_reconnect_storm",
]

ineligible = {}
eligible_raw = []
for adapter in inv.get("adapters", []):
    adapter_id = adapter["adapter_id"]
    for dev in adapter.get("devices", []):
        mac = dev["mac"]
        key = f"{adapter_id}|{mac}"
        reasons = []
        if key in pairing:
            reasons.append(pairing[key])
        if key in resume:
            reasons.append(resume[key])
        if key in power:
            reasons.append(power[key])
        if key in storm_blocked:
            reasons.append(storm_blocked[key])
        if reasons:
            reasons.sort(key=lambda r: reason_ladder.index(r))
            ineligible[key] = {"adapter_id": adapter_id, "mac": mac, "reason": reasons[0]}
        else:
            eligible_raw.append(
                {
                    "adapter_id": adapter_id,
                    "mac": mac,
                    "salted_id": dev.get("salted_id", ""),
                    "criticality": int(dev["criticality"]),
                    "gatt_service_count": int(gatt.get(key, 0)),
                    "reconnect_attempts": int(storm_attempts.get(key, 0)),
                }
            )

proc = subprocess.run(
    ["bash", "/app/lib/boltlane/criticality_lane/rank_by_criticality.sh"],
    input=json.dumps(eligible_raw).encode(),
    stdout=subprocess.PIPE,
    check=True,
)
ranked = json.loads(proc.stdout.decode())
for idx, row in enumerate(ranked, start=1):
    row["rank"] = idx

ineligible_rows = sorted(ineligible.values(), key=lambda r: (r["adapter_id"], r["mac"]))

ledger = {
    "run_id": run_id,
    "scenario": meta["scenario"],
    "load_seq": inv.get("load_seq", meta.get("load_seq", 1)),
    "fleet": inv["fleet"],
    "cutover_window_min": inv["cutover_window_min"],
    "eligible": ranked,
    "ineligible": ineligible_rows,
    "eligible_count": len(ranked),
    "ineligible_count": len(ineligible_rows),
}
Path("/app/state/reconnect-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
print(json.dumps({"ok": True, "eligible_count": ledger["eligible_count"]}))
PY
