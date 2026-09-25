#!/usr/bin/env bash
# Decoy focal length bump — not used on align export hot path.
set -euo pipefail

decoy_bump_focal() {
  local focal="$1"
  python3 - "$focal" <<'PY'
import sys
print(float(sys.argv[1]) * 1.05)
PY
}
