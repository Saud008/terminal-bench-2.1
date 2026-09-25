#!/usr/bin/env bash
# Legacy topological preview helper (not used by manifest publish — see linkorder.sh).

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
