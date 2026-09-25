#!/usr/bin/env bash
# Retired DFS mount helper — not used by workshop-plan.

legacy_mount_order() {
  local graph_file="$1"
  declare -A adj=()
  local from to opt
  while IFS=$'\t' read -r from to opt; do
    [[ -z "$from" || -z "$to" ]] && continue
    adj["$to"]+="${from} "
  done < "${graph_file}"
  local -a order=()
  local node
  for node in "${!adj[@]}"; do
    order+=("$node")
  done
  printf '%s\n' "${order[@]}"
}
