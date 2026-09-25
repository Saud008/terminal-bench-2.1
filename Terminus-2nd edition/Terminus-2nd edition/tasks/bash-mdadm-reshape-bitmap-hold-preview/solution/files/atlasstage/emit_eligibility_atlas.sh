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
cfg = json.loads(Path("/app/config/mdreshape.json").read_text())
if not output:
    output = cfg["default_output"]
ledger = json.loads(Path("/app/state/reshape-ledger.json").read_text())
eligible = ledger.get("eligible") or []
blocked = ledger.get("blocked") or []
eligible_names = ",".join(r["name"] for r in eligible)
blocked_pairs = ",".join(f'{r["name"]}:{r["block_reason"]}' for r in blocked)
payload = "|".join([
    "mdreshape|v1",
    run_id,
    ledger["scenario"],
    str(ledger["eligible_count"]),
    str(ledger["blocked_count"]),
    eligible_names,
    blocked_pairs,
])
digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
atlas = {
    "schema_version": 1,
    "run_id": run_id,
    "scenario": ledger["scenario"],
    "fleet": ledger["fleet"],
    "eligible": eligible,
    "blocked": blocked,
    "eligible_count": ledger["eligible_count"],
    "blocked_count": ledger["blocked_count"],
    "audit_digest": digest,
}
out = Path(output)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(atlas, indent=2) + "\n")
print(json.dumps({"ok": True, "output": str(out)}))
PY
