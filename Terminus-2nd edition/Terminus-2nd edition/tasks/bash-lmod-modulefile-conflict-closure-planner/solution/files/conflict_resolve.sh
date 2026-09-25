#!/bin/bash
# Conflict precedence: higher @priority wins; evicted module is unloaded first.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/resolve/dep_closure.sh"

_remove_from_final() {
  local -n arr="$1"
  local drop="$2"
  local -a kept=()
  local x
  for x in "${arr[@]}"; do
    [[ "${x}" != "${drop}" ]] && kept+=("${x}")
  done
  arr=("${kept[@]}")
}

apply_conflicts() {
  local -n _order="$1"
  local -n records_arr="$2"
  local -n _final="$3"
  local -n _unloads="$4"
  _final=()
  _unloads=()
  local -A loaded=()
  local m rec pri skip
  for m in "${_order[@]}"; do
    rec="$(lookup_record "${m}" records_arr)" || continue
    pri="$(record_field "${rec}" priority)"
    skip=0
    while true; do
      local evicted=0
      for other in "${!loaded[@]}"; do
        local conflicts other_rec other_conflicts other_pri
        conflicts="$(record_field "${rec}" conflicts)"
        other_rec="$(lookup_record "${other}" records_arr)"
        other_conflicts="$(record_field "${other_rec}" conflicts)"
        if [[ ",${conflicts}," == *",${other},"* ]] || [[ ",${other_conflicts}," == *",${m},"* ]]; then
          other_pri="$(record_field "${other_rec}" priority)"
          if (( pri > other_pri )); then
            unset 'loaded[$other]'
            _unloads+=("${other}")
            _remove_from_final _final "${other}"
            evicted=1
          elif (( pri < other_pri )); then
            skip=1
          else
            if [[ "${m}" < "${other}" ]]; then
              unset 'loaded[$other]'
              _unloads+=("${other}")
              _remove_from_final _final "${other}"
              evicted=1
            else
              skip=1
            fi
          fi
        fi
      done
      (( skip )) && break
      (( evicted )) || break
    done
    if (( skip )); then
      continue
    fi
    loaded["$m"]=1
    _final+=("${m}")
  done
}
