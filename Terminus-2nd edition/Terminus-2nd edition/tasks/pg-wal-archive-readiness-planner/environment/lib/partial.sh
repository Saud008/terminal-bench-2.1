#!/usr/bin/env bash
# Partial WAL segment handling.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

list_partial_files() {
  local archive="$1"
  find "${archive}" -maxdepth 1 -type f -name '*.partial' -printf '%f\n' | sort
}

partial_blocks_restore() {
  local archive="$1"
  local selected="$2"
  echo "[]"
}
