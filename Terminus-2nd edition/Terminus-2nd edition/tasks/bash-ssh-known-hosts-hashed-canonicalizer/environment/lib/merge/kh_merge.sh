#!/usr/bin/env bash
# Merge parsed records.

# shellcheck source=/app/lib/decoy/kh_sort_legacy.sh
source "${ROOT:-/app}/lib/decoy/kh_sort_legacy.sh"

kh__record_key() {
  local rec="$1"
  local sep=$'\x1f'
  local IFS="$sep"
  read -r revoked certauth kind plain salt hash port keytype keyblob comment <<< "$rec"
  if [[ "$kind" == "hashed" ]]; then
    printf '%s|%s|%s' "|1|${salt}|${hash}" "$keytype" "$keyblob"
  else
    printf '%s|%s|%s' "$plain" "$keytype" "$keyblob"
  fi
}

kh__sort_tuple() {
  local rec="$1"
  local sep=$'\x1f'
  local IFS="$sep"
  read -r revoked certauth kind plain salt hash port keytype keyblob comment <<< "$rec"
  printf '%s' "$keyblob"
}

kh__better_record() {
  local cur="$1"
  local new="$2"
  local sep=$'\x1f'
  local IFS="$sep"
  read -r cur_rev _ _ _ _ _ _ _ _ cur_comment <<< "$cur"
  read -r new_rev _ _ _ _ _ _ _ _ new_comment <<< "$new"

  if [[ "$cur_rev" != "$new_rev" ]]; then
    if [[ "$new_rev" == "0" ]]; then
      printf '%s' "$new"
      return
    fi
    printf '%s' "$cur"
    return
  fi

  if [[ "$new_comment" > "$cur_comment" ]]; then
    printf '%s' "$new"
  else
    printf '%s' "$cur"
  fi
}

kh_merge_records() {
  local merge_dup="${KH_MERGE_DUPLICATES:-1}"
  local -A merged=()
  local rec key
  for rec in "$@"; do
    [[ -z "$rec" ]] && continue
    if [[ "$merge_dup" == "0" ]]; then
      key="${RANDOM}${RANDOM}$(printf '%s' "$rec" | wc -c)"
    else
      key="$(kh__record_key "$rec")"
    fi
    if [[ -z "${merged[$key]:-}" ]]; then
      merged[$key]="$rec"
    else
      merged[$key]="$(kh__better_record "${merged[$key]}" "$rec")"
    fi
  done

  local -a keys=("${!merged[@]}")
  local -a sorted=()
  local k tuple rec
  for k in "${keys[@]}"; do
    sorted+=("$(kh__sort_tuple "${merged[$k]}")"$'\x1e'"${merged[$k]}")
  done

  local IFS=$'\n'
  sorted=($(printf '%s\n' "${sorted[@]}" | LC_ALL=C sort -t $'\x1e' -k1,1))

  local out=()
  local entry
  for entry in "${sorted[@]}"; do
    out+=("${entry#*$'\x1e'}")
  done
  printf '%s\n' "${out[@]}"
}
