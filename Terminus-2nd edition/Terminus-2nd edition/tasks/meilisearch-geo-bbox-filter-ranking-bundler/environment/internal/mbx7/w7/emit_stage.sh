#!/usr/bin/env bash
set -euo pipefail
RUN_ID=""; OUTPUT=""
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
cfg = json.loads(Path("/app/config/geoboxplay.json").read_text())
if not output: output = cfg["default_output"]
ledger = json.loads(Path("/app/state/round-score.json").read_text())
inv = json.loads(Path("/app/state/level-roster.json").read_text())
rows = sorted(ledger.get("admitted") or [], key=lambda r: int(r["admit_rank"]))
payload = "".join(r["doc_id"] + "\n" for r in rows)
atlas = dict(ledger)
atlas["atlas_digest"] = hashlib.sha256(payload.encode()).hexdigest()
atlas["focus_docs"] = inv.get("focus_docs") or []
out = Path(output); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(atlas, indent=2)+"\n")
print(json.dumps({"ok": True, "output": str(out)}))
PY
