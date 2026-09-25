#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

die() {
  echo "borg-prune-sim: $*" >&2
  exit 1
}

require_file() {
  local f="$1"
  [ -f "${f}" ] || die "file not found: ${f}"
}

stage_path_for() {
  local list_file="$1"
  echo "$(dirname "${list_file}")/borg.stage.json"
}

list_dir_for() {
  local list_file="$1"
  dirname "${list_file}"
}
