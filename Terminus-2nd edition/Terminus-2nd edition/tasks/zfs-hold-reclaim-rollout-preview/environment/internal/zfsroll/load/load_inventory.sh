#!/usr/bin/env bash
# Intentionally incomplete load_seq handling for the baseline image.
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
import json, os, sys
from pathlib import Path

scenario, run_id = sys.argv[1], sys.argv[2]
cfg = json.loads(Path("/app/config/zfshold.json").read_text())
fixture_dir = os.environ.get("TB3_FIXTURE_DIR") or cfg["fixture_dir"]
salt = os.environ.get("TB3_HOLD_SALT")
if salt is None or salt == "":
    salt = cfg.get("hold_name_salt") or ""
src = Path(fixture_dir) / scenario / "inventory.json"
inv = json.loads(src.read_text())
for ds in inv.get("datasets", []):
    holds = ds.get("holds") or []
    if salt:
        ds["holds"] = [h + salt for h in holds]
inv["load_seq"] = 1
state = Path(cfg["state_dir"])
state.mkdir(parents=True, exist_ok=True)
(state / "inventory.json").write_text(json.dumps(inv, indent=2) + "\n")
meta = {"scenario": scenario, "run_id": run_id, "load_seq": 1}
(state / "run-meta.json").write_text(json.dumps(meta, indent=2) + "\n")
print(json.dumps({"ok": True, "load_seq": 1}))
PY
