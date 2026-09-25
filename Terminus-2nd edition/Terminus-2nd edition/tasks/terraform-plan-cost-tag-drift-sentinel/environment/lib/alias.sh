#!/usr/bin/env bash
# BROKEN baseline: ignores provider_aliases map.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

resolve_provider_scope() {
  local provider_key="$1"
  local policy_path="$2"
  echo "${provider_key}"
}
