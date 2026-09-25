#!/usr/bin/env bash
# Decoy topological helper — reversed edge walk, not on workshop-plan hot path.

decoy_mount_order() {
  local graph_file="$1"
  declare -A rev=()
  local from to opt
  while IFS=$'\t' read -r from to opt; do
    [[ -z "$from" || -z "$to" ]] && continue
    rev["$to"]+="${from} "
  done < "${graph_file}"
  printf '%s\n' "${!rev[@]}"
}
