#!/usr/bin/env bash
# Decoy legacy preview sorter — NOT sourced by lt-canonicalize publish hot path.
# Agents who patch this file alone still fail linkorder dependency_order checks.

lt_topo_order() {
  local id="$1"
  local deps=()
  local dep
  while IFS= read -r dep; do
    [ -z "${dep}" ] && continue
    if lt_edge_removed "${id}" "${dep}"; then
      continue
    fi
    deps+=("${dep}")
  done < <(lt_direct_deps "${id}")
  if [ "${#deps[@]}" -eq 0 ]; then
    LT_TOPO_RESULT=()
    return 0
  fi
  local old_ifs="${IFS}"
  IFS=$'\n'
  deps=($(printf '%s\n' "${deps[@]}" | LC_ALL=C sort))
  IFS="${old_ifs}"
  LT_TOPO_RESULT=("${deps[@]}")
}
