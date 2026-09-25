#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

workspace_staging_path() {
  local ws_path="$1"
  local base
  base="$(basename "${ws_path}")"
  echo "${APP_ROOT}/stage/license-compliance/${base}.json"
}
