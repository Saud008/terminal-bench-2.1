#!/usr/bin/env bash
# Offline media ledger lookup after alias normalization.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/tc_policy.sh"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/reel_alias.sh"

ledger_contains() {
  local reel="$1"
  local missing_file="$2"
  local alias_file="$3"
  local check_name="${reel}"
  local line
  if [[ "${MISSING_BEFORE_ALIAS}" -eq 1 ]]; then
    check_name="${reel}"
  elif [[ "${MISSING_BEFORE_ALIAS}" -eq 0 ]]; then
    check_name="$(resolve_reel "${reel}" "${alias_file}")"
  fi
  if [[ ! -f "${missing_file}" ]]; then
    return 1
  fi
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line%%#*}"
    line="$(echo "${line}" | tr -d '[:space:]')"
    [[ -z "${line}" ]] && continue
    if [[ "${line}" == "${check_name}" ]]; then
      return 0
    fi
  done < "${missing_file}"
  return 1
}
