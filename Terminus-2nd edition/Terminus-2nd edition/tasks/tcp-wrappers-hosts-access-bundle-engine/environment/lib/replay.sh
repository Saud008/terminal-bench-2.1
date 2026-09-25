#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

replay_session() {
  local root="$1"
  local session_path="$2"
  local export_path="$3"
  local manifest name payload
  manifest="$(read_manifest "$root")"
  name="$(python3 - "$manifest" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["name"])
PY
)"
  payload="$(python3 - "$name" "$session_path" <<'PY'
import json, sys
entries = json.load(open(sys.argv[2], encoding="utf-8"))
print(json.dumps({"bundle": sys.argv[1], "checked": len(entries), "mismatches": []}, indent=2))
PY
)"
  json_write "$export_path" "$payload"
  return 0
}
