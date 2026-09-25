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
LIB=/app/internal/mbx7
PIN=$(bash "${LIB}/w1/gate_pin.sh")
BBOX=$(bash "${LIB}/w2/gate_rect.sh")
LAG=$(bash "${LIB}/w3/gate_lag.sh")
FLOOR=$(bash "${LIB}/w4/gate_floor.sh")
python3 - <<'PY' "$RUN_ID" "$PIN" "$BBOX" "$LAG" "$FLOOR"
import json, math, subprocess, sys
from pathlib import Path
run_id, pin_s, bbox_s, lag_s, floor_s = sys.argv[1:6]
pin, bbox, lag, floor = map(json.loads, (pin_s, bbox_s, lag_s, floor_s))
inv = json.loads(Path("/app/state/level-roster.json").read_text())
meta = json.loads(Path("/app/state/run-meta.json").read_text())

def hav(lon1, lat1, lon2, lat2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return 2*r*math.asin(min(1.0, math.sqrt(a)))

priority = ["blocked_pin","blocked_bbox","blocked_replica_lag","blocked_doc_floor","blocked_admit_cap"]
lag_ok = bool(lag.get("lag_ok")); focus = inv["focus"]; max_admit = int(inv["max_admit"])
denied = {}; candidates = []
for doc in inv.get("documents", []):
    if doc.get("kind") != "document":
        continue
    did = doc["doc_id"]; reasons = []
    if did in pin: reasons.append("blocked_pin")
    if did in bbox: reasons.append("blocked_bbox")
    if not lag_ok: reasons.append("blocked_replica_lag")
    if reasons:
        reasons.sort(key=lambda r: priority.index(r)); denied[did] = reasons[0]
    else:
        aff = 1.0 / (1.0 + hav(float(focus["lon"]), float(focus["lat"]), float(doc["lon"]), float(doc["lat"])))
        candidates.append({"doc_id": did, "lon": float(doc["lon"]), "lat": float(doc["lat"]), "affinity": aff, "capture_seq": int(doc.get("capture_seq", 0))})
# baseline skips floor quorum
proc = subprocess.run(["bash","/app/internal/mbx7/w5/rank_mix.sh"], input=json.dumps(candidates).encode(), stdout=subprocess.PIPE, check=True)
ranked = json.loads(proc.stdout.decode())
admitted = ranked[:max_admit]
for row in ranked[max_admit:]:
    denied[row["doc_id"]] = "blocked_admit_cap"
ledger = {
  "run_id": run_id, "level": meta["level"], "load_seq": inv.get("load_seq", meta.get("load_seq", 1)),
  "shard": inv["shard"], "admitted": admitted, "denied": [{"doc_id": n, "deny_reason": r} for n,r in sorted(denied.items())],
  "admitted_count": len(admitted), "denied_count": len(denied),
}
Path("/app/state/round-score.json").write_text(json.dumps(ledger, indent=2)+"\n")
print(json.dumps({"ok": True, "admitted_count": ledger["admitted_count"]}))
PY
