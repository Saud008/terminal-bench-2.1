#!/usr/bin/env bash
set -euo pipefail

ensure_runtime_dirs() {
  mkdir -p /app/state /app/output
}

sha256_hex() {
  printf '%s' "$1" | sha256sum | awk '{print $1}'
}

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<<"$1" | sed 's/^"//;s/"$//'
}
