#!/usr/bin/env bash
# Map provider_key to provider_scope via policy aliases.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

resolve_provider_scope() {
  local provider_key="$1"
  local policy_path="$2"
  jq -r --arg key "${provider_key}" '.provider_aliases[$key] // $key' "${policy_path}"
}
