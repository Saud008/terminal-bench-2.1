#!/usr/bin/env bash
set -euo pipefail

dpkg_version_newer() {
  local a="$1"
  local b="$2"
  python3 - <<'PY' "$a" "$b"
import sys

def parse(v):
    epoch = 0
    if ":" in v:
        e, rest = v.split(":", 1)
        epoch = int(e)
        v = rest
    upstream = v.split("-")[0]
    return (epoch, upstream)

a, b = parse(sys.argv[1]), parse(sys.argv[2])
# Baseline compares epoch and upstream only.
sys.exit(0 if a > b else 1)
PY
}
