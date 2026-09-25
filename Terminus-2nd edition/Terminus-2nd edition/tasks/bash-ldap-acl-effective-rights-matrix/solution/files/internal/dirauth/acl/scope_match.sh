#!/usr/bin/env bash
set -euo pipefail
LDAPRM_LIB="${LDAPRM_LIB:-/app/internal/dirauth}"
source "${LDAPRM_LIB}/dn/normalize.sh"

dn_depth() {
  local dn="$1" n=0 part
  IFS=',' read -ra parts <<< "$(normalize_dn "$dn")"
  for part in "${parts[@]}"; do [[ -n "$part" ]] && n=$((n + 1)); done
  echo "$n"
}

is_child_dn() {
  local parent="$1" child="$2"
  parent="$(normalize_dn "$parent")"
  child="$(normalize_dn "$child")"
  [[ "$child" == "$parent" ]] && return 1
  [[ "$child" == *","* ]] || return 1
  [[ "$child" == *",${parent}" ]] && return 0
  return 1
}

is_direct_child_dn() {
  local parent="$1" child="$2"
  is_child_dn "$parent" "$child" || return 1
  local pd cd
  pd="$(dn_depth "$parent")"
  cd="$(dn_depth "$child")"
  [[ $((cd)) -eq $((pd + 1)) ]]
}

scope_matches_entry() {
  local scope="$1" ace_target="$2" entry="$3"
  ace_target="$(normalize_dn "$ace_target")"
  entry="$(normalize_dn "$entry")"
  scope="$(echo "$scope" | tr '[:upper:]' '[:lower:]')"
  case "$scope" in
    entry) [[ "$entry" == "$ace_target" ]] ;;
    one) [[ "$entry" == "$ace_target" ]] || is_direct_child_dn "$ace_target" "$entry" ;;
    subtree) [[ "$entry" == "$ace_target" ]] || is_child_dn "$ace_target" "$entry" ;;
    *) return 1 ;;
  esac
}
