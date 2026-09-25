#!/usr/bin/env bash
# Legacy sort helper — not used for export ordering (see known-hosts-format.md).

kh_sort_key() {
  local rec="$1"
  local sep=$'\x1f'
  local IFS="$sep"
  read -r _ _ _ _ _ _ _ _ keyblob _ <<< "$rec"
  printf '%s' "$keyblob"
}

kh_sort_records() {
  local -a sorted=()
  local rec
  for rec in "$@"; do
    [[ -z "$rec" ]] && continue
    sorted+=("$(kh_sort_key "$rec")"$'\x1e'"${rec}")
  done
  local IFS=$'\n'
  sorted=($(printf '%s\n' "${sorted[@]}" | LC_ALL=C sort -t $'\x1e' -k1,1))
  local entry
  for entry in "${sorted[@]}"; do
    printf '%s\n' "${entry#*$'\x1e'}"
  done
}
