#!/bin/bash
# PATH and library path mutation ordering.
set -euo pipefail

source "${APP_ROOT}/lib/resolve/dep_closure.sh"

# Each mutation line: VAR|prepend|value  or VAR|append|value
build_path_mutations() {
  local -n _order="$1"
  local -n _recs="$2"
  local -n _muts="$3"
  _muts=()
  local m rec pre app chunk var val
  for m in "${_order[@]}"; do
    rec="$(lookup_record "${m}" _recs)" || continue
    pre="$(record_field "${rec}" prepends)"
    app="$(record_field "${rec}" appends)"
    IFS='|' read -ra pre_arr <<< "${pre}"
    for chunk in "${pre_arr[@]}"; do
      if [[ -z "${chunk}" ]]; then
        continue
      fi
      var="${chunk%% *}"
      val="${chunk#* }"
      _muts+=("${var}|prepend|${val}")
    done
    IFS='|' read -ra app_arr <<< "${app}"
    for chunk in "${app_arr[@]}"; do
      if [[ -z "${chunk}" ]]; then
        continue
      fi
      var="${chunk%% *}"
      val="${chunk#* }"
      _muts+=("${var}|append|${val}")
    done
  done
}

apply_path_stack() {
  local -n _muts="$1"
  local -n _final_paths="$2"
  declare -A prepend_stack=() append_stack=()
  local line var op val existing
  for line in "${_muts[@]}"; do
    IFS='|' read -r var op val <<< "${line}"
    if [[ "${op}" == prepend ]]; then
      existing="${prepend_stack[$var]-}"
      if [[ -n "${existing}" ]]; then
        prepend_stack["${var}"]="${val}:${existing}"
      else
        prepend_stack["${var}"]="${val}"
      fi
    else
      existing="${append_stack[$var]-}"
      if [[ -n "${existing}" ]]; then
        append_stack["${var}"]="${existing}:${val}"
      else
        append_stack["${var}"]="${val}"
      fi
    fi
  done
  _final_paths=()
  local k
  for k in "${!prepend_stack[@]}"; do
    _final_paths+=("${k}|${prepend_stack[$k]}|${append_stack[$k]-}")
  done
}
