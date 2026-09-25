#!/usr/bin/env bash
set -euo pipefail
CORPUS=""; RUN_ID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --level) CORPUS="$2"; shift 2 ;;
    --run-id) RUN_ID="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$CORPUS" && -n "$RUN_ID" ]] || { echo "missing args" >&2; exit 2; }
python3 - <<'PY' "$CORPUS" "$RUN_ID"
import json, os, sys
from pathlib import Path
level, run_id = sys.argv[1], sys.argv[2]
cfg = json.loads(Path("/app/config/geoboxplay.json").read_text())
root = os.environ.get("TB3_LEVEL_DIR") or cfg["level_dir"]
salt = os.environ.get("TB3_PLAY_SALT")
if salt is None or salt == "":
    salt = cfg.get("pin_name_salt") or ""
inv = json.loads((Path(root) / level / "inventory.json").read_text())
for doc in inv.get("documents", []):
    pins = doc.get("filter_pins") or []
    if salt:
        doc["filter_pins"] = [p + salt for p in pins]
inv["load_seq"] = 1
state = Path(cfg["state_dir"]); state.mkdir(parents=True, exist_ok=True)
(state / "level-roster.json").write_text(json.dumps(inv, indent=2) + "\n")
(state / "run-meta.json").write_text(json.dumps({"level": level, "run_id": run_id, "load_seq": 1}, indent=2) + "\n")
print(json.dumps({"ok": True, "load_seq": 1}))
PY
