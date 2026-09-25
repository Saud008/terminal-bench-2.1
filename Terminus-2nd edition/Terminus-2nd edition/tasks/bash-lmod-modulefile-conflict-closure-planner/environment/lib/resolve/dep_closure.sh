#!/bin/bash
# Dependency closure walk for requested module loads.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common/records.sh"

closure_load_order() {
  local -n req_modules="$1"
  local -n records_arr="$2"
  local -n order_out="$3"
  order_out=()
  local -A seen=()
  local visit
  visit() {
    local m="$1"
    [[ -n "${seen[$m]+x}" ]] && return
    seen["$m"]=1
    local rec deps dep
    rec="$(lookup_record "${m}" records_arr)" || return 0
    # Baseline: emits module before visiting prerequisites.
    order_out+=("${m}")
    deps="$(record_field "${rec}" depends)"
    IFS=',' read -ra dep_arr <<< "${deps}"
    for dep in "${dep_arr[@]}"; do
      [[ -n "${dep}" ]] && visit "${dep}"
    done
  }
  local m
  for m in "${req_modules[@]}"; do
    visit "${m}"
  done
}
