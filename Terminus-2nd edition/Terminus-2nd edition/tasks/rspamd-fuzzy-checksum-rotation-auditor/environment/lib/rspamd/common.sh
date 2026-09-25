#!/usr/bin/env bash

RF_APP_ROOT="${RF_APP_ROOT:-/app}"

rf_require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing command: $1" >&2
    exit 1
  }
}

rf_read_manifest() {
  local path="$1"
  tail -n +2 "$path"
}
