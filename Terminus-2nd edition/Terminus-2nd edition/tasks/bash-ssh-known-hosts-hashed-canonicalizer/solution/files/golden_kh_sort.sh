#!/usr/bin/env bash
# Legacy sort helper — correct but not wired into export ordering.

kh_sort_key() {
  local rec="$1"
  local sep=$'\x1f'
  local IFS="$sep"
  read -r revoked certauth kind plain salt hash port keytype keyblob comment <<< "$rec"
  local cls=0
  [[ "$kind" == "hashed" ]] && cls=1
  local host_key=""
  if [[ "$kind" == "hashed" ]]; then
    host_key="$salt"
  else
    host_key="$(kh__plain_sort_key "$plain")"
  fi
  printf '%s|%s|%s|%s|%s' "$cls" "$host_key" "$port" "$keytype" "$revoked"
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
