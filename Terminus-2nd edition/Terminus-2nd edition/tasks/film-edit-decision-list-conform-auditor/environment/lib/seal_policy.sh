#!/usr/bin/env bash
# Seal digest and emit reopen policy helpers.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/tc_policy.sh"

compute_seal_digest() {
  local event_file="$1"
  local finding_file="$2"
  sha256sum "${event_file}" | awk '{print $1}'
}

emit_reopens_bundle() {
  [[ "${EMIT_REOPEN}" -eq 1 ]]
}
