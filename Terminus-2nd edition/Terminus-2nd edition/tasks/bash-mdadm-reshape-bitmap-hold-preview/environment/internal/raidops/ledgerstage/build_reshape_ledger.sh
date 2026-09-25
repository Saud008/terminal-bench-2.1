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

LIB=/app/internal/raidops
BITMAP_JSON=$(bash "${LIB}/policies/bitmap_policy.sh")
SPARE_JSON=$(bash "${LIB}/policies/spare_hold_policy.sh")
DEGRADED_JSON=$(bash "${LIB}/policies/degraded_floor_policy.sh")
LEVEL_JSON=$(bash "${LIB}/policies/level_path_policy.sh")
WINDOW_JSON=$(bash "${LIB}/policies/window_fit_policy.sh")

python3 - <<'PY' "$RUN_ID" "$BITMAP_JSON" "$SPARE_JSON" "$DEGRADED_JSON" "$LEVEL_JSON" "$WINDOW_JSON"
import json, subprocess, sys
from pathlib import Path

run_id, bitmap_s, spare_s, degraded_s, level_s, window_s = sys.argv[1:7]
bitmap = json.loads(bitmap_s)
spare = json.loads(spare_s)
degraded = json.loads(degraded_s)
level = json.loads(level_s)
window = json.loads(window_s)
inv = json.loads(Path("/app/state/inventory.json").read_text())
meta = json.loads(Path("/app/state/run-meta.json").read_text())

priority = [
    "blocked_bitmap",
    "blocked_spare_hold",
    "blocked_degraded",
    "blocked_illegal_path",
    "blocked_window",
]

blocked = {}
eligible_raw = []
for arr in inv.get("arrays", []):
    name = arr["name"]
    reasons = []
    if name in bitmap:
        reasons.append("blocked_bitmap")
    if name in spare:
        reasons.append("blocked_spare_hold")
    if name in degraded:
        reasons.append("blocked_degraded")
    if name in level:
        reasons.append("blocked_illegal_path")
    if name in window:
        reasons.append("blocked_window")
    if reasons:
        reasons.sort(key=lambda r: priority.index(r))
        blocked[name] = reasons[0]
    else:
        eligible_raw.append(
            {
                "name": name,
                "salted_name": arr.get("salted_name", ""),
                "criticality": int(arr["criticality"]),
                "level": arr["level"],
                "target_level": arr["target_level"],
            }
        )

proc = subprocess.run(
    ["bash", "/app/internal/raidops/ranking/criticality_rank.sh"],
    input=json.dumps(eligible_raw).encode(),
    stdout=subprocess.PIPE,
    check=True,
)
eligible = json.loads(proc.stdout.decode())
blocked_rows = [{"name": n, "block_reason": r} for n, r in sorted(blocked.items())]
ledger = {
    "run_id": run_id,
    "scenario": meta["scenario"],
    "load_seq": inv.get("load_seq", meta.get("load_seq", 1)),
    "fleet": inv["fleet"],
    "window_hours": inv["window_hours"],
    "eligible": eligible,
    "blocked": blocked_rows,
    "eligible_count": len(eligible),
    "blocked_count": len(blocked_rows),
}
Path("/app/state/reshape-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
print(json.dumps({"ok": True, "eligible_count": ledger["eligible_count"]}))
PY
