#!/usr/bin/env bash
set -euo pipefail

cidrs_overlap() {
  local a="$1"
  local b="$2"
  python3 - <<'PY' "$a" "$b"
import sys

a, b = sys.argv[1], sys.argv[2]
net_a = a.split("/")[0]
net_b = b.split("/")[0]
sys.exit(0 if net_a.startswith(net_b[:8]) or net_b.startswith(net_a[:8]) else 1)
PY
}
