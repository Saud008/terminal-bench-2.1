#!/usr/bin/env bash
# Shared helpers for systemd-timer-planner.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

die() {
  echo "systemd-timer-planner: $*" >&2
  exit 1
}

require_file() {
  local f="$1"
  [ -f "${f}" ] || die "file not found: ${f}"
}

require_dir() {
  local d="$1"
  [ -d "${d}" ] || die "directory not found: ${d}"
}

manifest_path_for() {
  local bundle="$1"
  local base
  base="$(basename "${bundle}")"
  echo "/app/stage/manifests/${base}.json"
}

bundle_timer_name() {
  local bundle="$1"
  basename "${bundle}" .timer.bundle
}
