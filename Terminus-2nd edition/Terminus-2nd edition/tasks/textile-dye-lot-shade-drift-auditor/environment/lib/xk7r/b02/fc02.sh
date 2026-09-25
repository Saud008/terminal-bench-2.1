#!/usr/bin/env bash
set -euo pipefail

cie76_delta() {
  python3 - "$@" <<'PY'
import sys
l1, a1, b1, l2, a2, b2 = map(float, sys.argv[1:])
dl = l1 - l2
da = a1 - a2
db = b1 - b2
print(f"{dl*dl + da*da + db*db:.6f}")
PY
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  cie76_delta "$@"
fi
