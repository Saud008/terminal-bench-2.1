#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

config_dir="$1"
output_path="$2"

filters="$(config_path "$config_dir" filters.conf)"
graph="$(config_path "$config_dir" graph.conf)"
rewrites="$(config_path "$config_dir" rewrites.conf)"

rewrite_refs=""
while IFS='|' read -r _ ref _; do
  [ -z "$ref" ] && continue
  rewrite_refs="${rewrite_refs}${ref} "
done < "$rewrites"

filter_exists() {
  grep -q "^${1}|" "$filters"
}

rewrite_uses() {
  [[ " ${rewrite_refs} " == *" ${1} "* ]]
}

: > "$output_path"
while IFS='|' read -r route_id filter_id dest fallback dead; do
  [ -z "$route_id" ] && continue
  filter_exists "$filter_id" || continue
  if [ "$dead" = "1" ] && [ "$fallback" = "0" ] && ! rewrite_uses "$filter_id"; then
    continue
  fi
  echo "${route_id}|${filter_id}|${dest}|${fallback}|${dead}" >> "$output_path"
done < "$graph"
