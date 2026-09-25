#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

pick_rendering_intent() {
  local profile_path="$1"
  local policy_path="$2"
  python3 - "${profile_path}" "${policy_path}" <<'PY'
import json, sys
from pathlib import Path

profile = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
policy = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
supported = set(profile.get("rendering_intents", {}).keys())
for intent in policy.get("intent_precedence", []):
    if intent in supported:
        print(intent)
        raise SystemExit(0)
print("")
PY
}

reference_lab_json() {
  local profile_path="$1"
  local patch_id="$2"
  local intent="$3"
  python3 - "${profile_path}" "${patch_id}" "${intent}" <<'PY'
import json, sys
from pathlib import Path

profile = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
patch_id = sys.argv[2]
intent = sys.argv[3]
intent_map = profile.get("rendering_intents", {}).get(intent, {})
if patch_id in intent_map:
    row = intent_map[patch_id]
elif patch_id in profile.get("reference_patches", {}):
    row = profile["reference_patches"][patch_id]
else:
    print("null")
    raise SystemExit(0)
print(json.dumps({"L": float(row["L"]), "a": float(row["a"]), "b": float(row["b"])}, separators=(",", ":")))
PY
}
