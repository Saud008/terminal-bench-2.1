#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

cie76_delta() {
  local l1="$1" a1="$2" b1="$3" l2="$4" a2="$5" b2="$6"
  python3 - "${l1}" "${a1}" "${b1}" "${l2}" "${a2}" "${b2}" <<'PY'
import math, sys
l1, a1, b1, l2, a2, b2 = map(float, sys.argv[1:])
print(f"{math.sqrt((l1-l2)**2 + (a1-a2)**2 + (b1-b2)**2):.6f}")
PY
}
