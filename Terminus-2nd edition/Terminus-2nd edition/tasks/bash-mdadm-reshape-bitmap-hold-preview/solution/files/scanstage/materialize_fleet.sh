#!/usr/bin/env bash
set -euo pipefail

SCENARIO=""
RUN_ID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) SCENARIO="$2"; shift 2 ;;
    --run-id) RUN_ID="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$SCENARIO" && -n "$RUN_ID" ]] || { echo "missing --scenario/--run-id" >&2; exit 2; }

python3 - <<'PY' "$SCENARIO" "$RUN_ID"
import hashlib, json, os, sys
from pathlib import Path

scenario, run_id = sys.argv[1], sys.argv[2]
cfg = json.loads(Path("/app/config/mdreshape.json").read_text())
fixture_dir = os.environ.get("TB3_SCENARIO_DIR") or cfg["fixture_dir"]
src = Path(fixture_dir) / scenario / "inventory.json"
inv = json.loads(src.read_text())

host_salt = inv.get("host_salt") or ""
for arr in inv.get("arrays", []):
    digest = hashlib.sha256((host_salt + ":" + arr["name"]).encode("utf-8")).hexdigest()
    arr["salted_name"] = digest[:16]

state = Path(cfg["state_dir"])
state.mkdir(parents=True, exist_ok=True)
prev_path = state / "inventory.json"
load_seq = 1
if prev_path.exists():
    try:
        prev = json.loads(prev_path.read_text())
        load_seq = int(prev.get("load_seq", 0)) + 1
    except Exception:
        load_seq = 1
inv["load_seq"] = load_seq
prev_path.write_text(json.dumps(inv, indent=2) + "\n")
meta = {"scenario": scenario, "run_id": run_id, "load_seq": load_seq}
(state / "run-meta.json").write_text(json.dumps(meta, indent=2) + "\n")
print(json.dumps({"ok": True, "load_seq": load_seq}))
PY
