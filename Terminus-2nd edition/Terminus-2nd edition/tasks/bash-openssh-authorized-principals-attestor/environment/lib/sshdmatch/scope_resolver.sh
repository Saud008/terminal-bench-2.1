#!/usr/bin/env bash
set -euo pipefail

SSHAP_LIB="${SSHAP_LIB:-/app/lib}"
source "${SSHAP_LIB}/common.sh"

resolve_match_scope() {
  local match_dir="$1" user="$2" host="$3"
  local f line scope="global" mu="" mh="" cur="" best_rank=0 cur_rank=0
  for f in "$match_dir"/*.match; do
    [[ -f "$f" ]] || continue
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" =~ ^Match ]]; then
        mu="$(echo "$line" | sed -n 's/.*User \([^,]*\).*/\1/p')"
        mh="$(echo "$line" | sed -n 's/.*Host \([^,]*\).*/\1/p')"
        cur=""
        cur_rank=0
        [[ -n "$mu" ]] && cur_rank=$((cur_rank + 1))
        [[ -n "$mh" ]] && cur_rank=$((cur_rank + 1))
      elif [[ "$line" =~ AuthorizedPrincipalsFile ]]; then
        cur="$(echo "$line" | awk '{print $2}')"
        cur="${cur#/app/fixtures/principals/}"
        cur="${cur%.principals}"
      fi
      if [[ -n "$cur" && -n "$mu" && -n "$mh" ]]; then
        if fnmatch_case "$mu" "$user" && fnmatch_case "$mh" "$host"; then
          if [[ "$cur_rank" -le "$best_rank" || "$best_rank" -eq 0 ]]; then
            best_rank="$cur_rank"
            scope="$cur"
          fi
        fi
      fi
    done < "$f"
  done
  echo "$scope"
}
