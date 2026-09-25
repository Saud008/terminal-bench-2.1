#!/usr/bin/env bash
# Compute source handle frame budgets with pull-down adjustment.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/tc_policy.sh"

handle_frame_budget() {
  local src_in="$1"
  local src_out="$2"
  local fps="$3"
  local pulldown="$4"
  local in_frames out_frames budget scale
  # shellcheck source=/dev/null
  source "${APP_ROOT}/lib/tc_convert.sh"
  in_frames="$(tc_to_frames "${src_in}" "${fps}" false)"
  out_frames="$(tc_to_frames "${src_out}" "${fps}" false)"
  budget=$(( out_frames - in_frames ))
  if [[ "${pulldown}" == "23976" ]]; then
    scale="${PULLDOWN_NUMERATOR}"
    if [[ "${scale}" -eq 23976 ]]; then
      budget=$(( (budget * 24000 + 11988) / 23976 ))
    fi
  fi
  printf '%s\n' "${budget}"
}
