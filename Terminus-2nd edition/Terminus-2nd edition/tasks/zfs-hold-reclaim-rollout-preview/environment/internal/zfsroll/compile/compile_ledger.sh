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

LIB=/app/internal/zfsroll
HOLD_JSON=$(bash "${LIB}/gates/hold_gate.sh")
CLONE_JSON=$(bash "${LIB}/gates/clone_gate.sh")
BOOK_JSON=$(bash "${LIB}/gates/bookmark_gate.sh")
FLOOR_JSON=$(bash "${LIB}/gates/pool_floor.sh")

python3 - <<'PY' "$RUN_ID" "$HOLD_JSON" "$CLONE_JSON" "$BOOK_JSON" "$FLOOR_JSON"
import json, subprocess, sys
from pathlib import Path

run_id, hold_s, clone_s, book_s, floor_s = sys.argv[1:6]
hold = json.loads(hold_s)
clone = json.loads(clone_s)
book = json.loads(book_s)
floor = json.loads(floor_s)
inv = json.loads(Path("/app/state/inventory.json").read_text())
meta = json.loads(Path("/app/state/run-meta.json").read_text())

priority = ["blocked_hold", "blocked_clone", "blocked_bookmark", "blocked_pool_floor"]
floor_ok = bool(floor.get("floor_ok"))

blocked = {}
eligible_raw = []
for ds in inv.get("datasets", []):
    if ds.get("kind") != "snapshot":
        continue
    name = ds["name"]
    reasons = []
    if name in hold:
        reasons.append("blocked_hold")
    if name in clone:
        reasons.append("blocked_clone")
    if name in book:
        reasons.append("blocked_bookmark")
    if not floor_ok:
        reasons.append("blocked_pool_floor")
    if reasons:
        reasons.sort(key=lambda r: priority.index(r))
        blocked[name] = reasons[0]
    else:
        eligible_raw.append({
            "name": name,
            "depth": int(ds["depth"]),
            "creation_txg": int(ds["creation_txg"]),
        })

proc = subprocess.run(
    ["bash", "/app/internal/zfsroll/order/reclaim_sort.sh"],
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
    "pool": inv["pool"],
    "free_pct": inv["free_pct"],
    "floor_pct": inv["floor_pct"],
    "eligible": eligible,
    "blocked": blocked_rows,
    "eligible_count": len(eligible),
    "blocked_count": len(blocked_rows),
}
Path("/app/state/reclaim-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
print(json.dumps({"ok": True, "eligible_count": ledger["eligible_count"]}))
PY
