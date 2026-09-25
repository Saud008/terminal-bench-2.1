#!/usr/bin/env bash
# Shared helpers for borg-prune-sim.
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
  echo "/app/state/borg.stage.json"
}

list_dir_for() {
  local list_file="$1"
  dirname "${list_file}"
}
