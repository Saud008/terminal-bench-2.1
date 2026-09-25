#!/usr/bin/env bash
set -euo pipefail
LDAPRM_LIB="${LDAPRM_LIB:-/app/internal/dirauth}"
source "${LDAPRM_LIB}/dn/normalize.sh"
source "${LDAPRM_LIB}/acl/scope_match.sh"

ace_sort_key() {
  local ace_line="$1"
  local src idx target scope inherit effect subj_type subj rights attrs depth scope_w deny_w user_w ace_id
  IFS='|' read -r src block_id idx target scope inherit effect subj_type subj rights attrs <<< "$ace_line"
  ace_id="${src}:${block_id}:${idx}"
  depth="$(dn_depth "$target")"
  case "$scope" in
    entry) scope_w=300 ;;
    one) scope_w=200 ;;
    *) scope_w=100 ;;
  esac
  deny_w=0
  [[ "$effect" == "allow" ]] && deny_w=1
  user_w=0
  [[ "$subj_type" == "group" ]] && user_w=1
  printf '%04d|%03d|%d|%d|%s' "$((9999 - depth))" "$scope_w" "$user_w" "$deny_w" "$ace_id"
}

sort_ace_lines() {
  local line key
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    key="$(ace_sort_key "$line")"
    echo "${key}|${line}"
  done | LC_ALL=C sort | sed 's/^[^|]*|[^|]*|[^|]*|[^|]*|[^|]*|//'
}
