#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

profile_checksum_hex() {
  local profile_path="$1"
  python3 - "${profile_path}" <<'PY'
import hashlib, json, sys
from pathlib import Path

profile = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
fields = profile.get("checksum_fields", [])
subset = {k: profile[k] for k in fields if k in profile}
payload = json.dumps(subset, sort_keys=True, separators=(",", ":")).encode("utf-8")
print(hashlib.sha256(payload).hexdigest())
PY
}

profile_checksum_ok() {
  local profile_path="$1"
  local stored computed
  stored="$(jq -r '.checksum // ""' "${profile_path}")"
  computed="$(profile_checksum_hex "${profile_path}")"
  [[ "${stored}" == "${computed}" ]]
}
