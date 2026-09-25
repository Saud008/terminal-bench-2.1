#!/usr/bin/env bash
# BROKEN baseline: checksum includes checksum field in hash input.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

profile_checksum_hex() {
  local profile_path="$1"
  python3 - "${profile_path}" <<'PY'
import hashlib, sys
from pathlib import Path

payload = Path(sys.argv[1]).read_bytes()
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
