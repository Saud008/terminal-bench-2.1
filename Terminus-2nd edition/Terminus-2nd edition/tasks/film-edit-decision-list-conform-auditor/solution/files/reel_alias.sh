#!/usr/bin/env bash
# Resolve reel aliases from alias map files (alias vault_id pairs).
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/tc_policy.sh"

resolve_reel() {
  local reel="$1"
  local map_file="$2"
  local line alias vault_id
  if [[ ! -f "${map_file}" ]]; then
    printf '%s\n' "${reel}"
    return 0
  fi
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line%%#*}"
    line="$(echo "${line}" | tr -d '[:space:]')"
    [[ -z "${line}" ]] && continue
    alias="${line%%=*}"
    vault_id="${line#*=}"
    if [[ "${reel}" == "${alias}" ]]; then
      printf '%s\n' "${vault_id}"
      return 0
    fi
    if [[ "${ALIAS_BIDIRECTIONAL}" -eq 1 && "${reel}" == "${vault_id}" ]]; then
      printf '%s\n' "${alias}"
      return 0
    fi
  done < "${map_file}"
  printf '%s\n' "${reel}"
}
