#!/usr/bin/env bash
# Missing media inventory checks and suppression policy.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/tc_policy.sh"

is_missing_reel() {
  local reel="$1"
  local missing_file="$2"
  local alias_file="$3"
  local line check_name resolved
  check_name="${reel}"
  if [[ "${MISSING_BEFORE_ALIAS}" -eq 0 ]]; then
    # shellcheck source=/dev/null
    source "${APP_ROOT}/lib/reel_alias.sh"
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

should_suppress_missing() {
  local reel="$1"
  local missing_file="$2"
  local alias_file="$3"
  if is_missing_reel "${reel}" "${missing_file}" "${alias_file}"; then
    return 0
  fi
  return 1
}
