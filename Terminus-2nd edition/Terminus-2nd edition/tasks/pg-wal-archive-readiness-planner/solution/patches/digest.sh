#!/usr/bin/env bash
# Staging digest helper.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

staging_digest() {
  local payload="$1"
  python3 - "${payload}" <<'PY'
import hashlib, json, sys
data = json.loads(sys.argv[1])
print(hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16])
PY
}
