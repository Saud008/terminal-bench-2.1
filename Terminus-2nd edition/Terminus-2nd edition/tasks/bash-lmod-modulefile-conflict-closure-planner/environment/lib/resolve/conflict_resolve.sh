#!/bin/bash
# Conflict precedence: higher @priority wins; evicted module is unloaded first.
set -euo pipefail

source "${APP_ROOT}/lib/resolve/dep_closure.sh"

apply_conflicts() {
  local -n _order="$1"
  local -n _recs="$2"
  local -n _final="$3"
  local -n _unloads="$4"
  _final=()
  _unloads=()
  local -A loaded=()
  local m rec pri other other_pri other_rec other_conflicts skip
  for m in "${_order[@]}"; do
    rec="$(lookup_record "${m}" _recs)" || continue
    pri="$(record_field "${rec}" priority)"
    skip=0
    while true; do
      local blocked=0
      for other in "${!loaded[@]}"; do
        local conflicts
        conflicts="$(record_field "${rec}" conflicts)"
        other_rec="$(lookup_record "${other}" _recs)"
        other_conflicts="$(record_field "${other_rec}" conflicts)"
        if [[ ",${conflicts}," == *",${other},"* ]] || [[ ",${other_conflicts}," == *",${m},"* ]]; then
          other_pri="$(record_field "${other_rec}" priority)"
          # Baseline: lower-priority module may remain when priorities differ.
          if (( other_pri > pri )); then
            unset 'loaded[$other]'
            _unloads+=("${other}")
          else
            skip=1
            blocked=1
          fi
        fi
      done
      [[ "${blocked}" -eq 0 ]] && break
      [[ "${skip}" -eq 1 ]] && break
    done
    if (( skip )); then
      continue
    fi
    loaded["$m"]=1
    _final+=("${m}")
  done
}
