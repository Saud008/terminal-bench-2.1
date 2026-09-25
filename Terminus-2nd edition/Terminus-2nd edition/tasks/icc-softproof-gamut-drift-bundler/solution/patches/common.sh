#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

die() {
  echo "icc-drift-bundler: $*" >&2
  exit 1
}

require_file() {
  local f="$1"
  [ -f "${f}" ] || die "file not found: ${f}"
}

stage_path_for() {
  local readings_file="$1"
  echo "$(dirname "${readings_file}")/icc.stage.json"
}
