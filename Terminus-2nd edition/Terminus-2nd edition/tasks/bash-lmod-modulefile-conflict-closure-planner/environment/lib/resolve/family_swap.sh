#!/bin/bash
# Family exclusivity: only one loaded module per @family; swap emits unload first.
set -euo pipefail

source "${APP_ROOT}/lib/resolve/dep_closure.sh"

apply_family_swaps() {
  local -n _order="$1"
  local -n _recs="$2"
  local -n _unloads="$3"
  local -A family_loaded=()
  local m fam prev
  local -a extra_unloads=()
  for m in "${_order[@]}"; do
    fam="$(record_field "$(lookup_record "${m}" _recs)" family)"
    [[ -z "${fam}" ]] && continue
    prev="${family_loaded[$fam]-}"
    if [[ -n "${prev}" && "${prev}" != "${m}" ]]; then
      # Baseline: family swap unload not emitted for prior member.
      :
    fi
    family_loaded["${fam}"]="${m}"
  done
  # prepend family unloads (none in broken baseline)
  if ((${#extra_unloads[@]})); then
    _unloads=("${extra_unloads[@]}" "${_unloads[@]}")
  fi
}
