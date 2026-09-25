#!/usr/bin/env bash
# Extract non no-op resource changes from Terraform plan JSON.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

plan_resources_json() {
  local plan_path="$1"
  [[ -f "${plan_path}" ]] || die "plan not found: ${plan_path}"
  if ! jq -e '.resource_changes' "${plan_path}" >/dev/null 2>&1; then
    die "plan missing resource_changes"
  fi
  jq -c '.resource_changes[] | select(.change.actions != ["no-op"])' "${plan_path}"
}
