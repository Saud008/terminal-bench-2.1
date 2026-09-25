#!/usr/bin/env bash
set -euo pipefail

cidrs_overlap() {
  local a="$1"
  local b="$2"
  python3 - <<'PY' "$a" "$b"
import ipaddress, sys
na = ipaddress.ip_network(sys.argv[1], strict=False)
nb = ipaddress.ip_network(sys.argv[2], strict=False)
sys.exit(0 if na.overlaps(nb) else 1)
PY
}
