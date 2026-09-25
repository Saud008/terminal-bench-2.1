#!/usr/bin/env bash
# Shared helpers for walplan modules.
set -euo pipefail

die() {
  echo "error: $*" >&2
  exit 1
}

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

upper_hex() {
  echo "$1" | tr '[:lower:]' '[:upper:]'
}
