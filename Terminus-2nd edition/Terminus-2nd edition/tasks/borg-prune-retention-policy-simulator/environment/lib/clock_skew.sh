#!/usr/bin/env bash
# Clock-skew normalization helpers.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

normalize_timestamp() {
  local ts="$1"
  local ref="$2"
  local skew="$3"
  echo "${ts}"
  return 1
}
