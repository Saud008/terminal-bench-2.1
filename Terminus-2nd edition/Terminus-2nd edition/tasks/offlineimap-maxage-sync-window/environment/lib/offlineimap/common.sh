#!/usr/bin/env bash

OI_APP_ROOT="${OI_APP_ROOT:-/app}"

oi_require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "offlineimap: missing command: $1" >&2
    return 1
  }
}

oi_read_manifest() {
  local manifest="$1"
  [[ -f "${manifest}" ]] || {
    echo "offlineimap: manifest not found: ${manifest}" >&2
    return 1
  }
  tail -n +2 "${manifest}"
}
