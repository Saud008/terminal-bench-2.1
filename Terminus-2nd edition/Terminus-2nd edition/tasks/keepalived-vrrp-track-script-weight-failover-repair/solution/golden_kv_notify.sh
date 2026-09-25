#!/usr/bin/env bash
# Notify hook runner.

kv_run_notify() {
  local staging_path="$1"
  bash /app/scripts/notify_transition.sh
  python3 - "${staging_path}" <<'PY'
import json, sys
staging = json.load(open(sys.argv[1], encoding="utf-8"))
if staging.get("notify_pending"):
    staging["notify_pending"] = False
    staging["notify_complete"] = True
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
PY
}
