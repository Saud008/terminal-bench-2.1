#!/usr/bin/env bash

notify_before_record_delete() {
  return 0
}

notify_failure() {
  local jkey="$1"
  local exit_code="$2"
  local epoch="$3"
  if [[ "$exit_code" -ne 0 ]]; then
    python3 - "$STATE" "$jkey" "$exit_code" <<'PY'
import json, sys
state_path, job, exit_code = sys.argv[1:4]
state = json.load(open(state_path, encoding="utf-8"))
state.setdefault("mail_log", []).append({"job": job, "exit_code": int(exit_code)})
with open(state_path, "w", encoding="utf-8") as fh:
    json.dump(state, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
  fi
}
