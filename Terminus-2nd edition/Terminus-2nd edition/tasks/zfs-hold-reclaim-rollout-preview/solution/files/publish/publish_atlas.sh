#!/usr/bin/env bash
set -euo pipefail

RUN_ID=""
OUTPUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$RUN_ID" ]] || { echo "missing --run-id" >&2; exit 2; }

python3 - <<'PY' "$RUN_ID" "$OUTPUT"
import hashlib, json, sys
from pathlib import Path

run_id, output = sys.argv[1], sys.argv[2]
cfg = json.loads(Path("/app/config/zfshold.json").read_text())
if not output:
    output = cfg["default_output"]
ledger = json.loads(Path("/app/state/reclaim-ledger.json").read_text())
inv = json.loads(Path("/app/state/inventory.json").read_text())
eligible = sorted(ledger.get("eligible") or [], key=lambda r: int(r["reclaim_rank"]))
names = [r["name"] for r in eligible]
payload = "".join(n + "\n" for n in names)
digest = hashlib.sha256(payload.encode()).hexdigest()
atlas = dict(ledger)
atlas["audit_digest"] = digest
atlas["focus_snapshots"] = inv.get("focus_snapshots") or []
out = Path(output)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(atlas, indent=2) + "\n")
print(json.dumps({"ok": True, "output": str(out)}))
PY
