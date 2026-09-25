#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

config_dir="$1"
input_path="$2"
output_path="$3"

filters="$(config_path "$config_dir" filters.conf)"
graph="$(config_path "$config_dir" graph.conf)"
rewrites="$(config_path "$config_dir" rewrites.conf)"

rewrite_refs=""
while IFS='|' read -r _ ref _; do
  [ -z "$ref" ] && continue
  rewrite_refs="${rewrite_refs}${ref} "
done < "$rewrites"

filter_exists() {
  local fid="$1"
  grep -q "^${fid}|" "$filters"
}

rewrite_uses() {
  local fid="$1"
  [[ " ${rewrite_refs} " == *" ${fid} "* ]]
}

: > "$output_path"
while IFS='|' read -r route_id filter_id dest fallback dead; do
  [ -z "$route_id" ] && continue
  filter_exists "$filter_id" || continue
  if [ "$dead" = "1" ] && [ "$fallback" = "1" ]; then
    continue
  fi
  echo "${route_id}|${filter_id}|${dest}|${fallback}|${dead}" >> "$output_path"
done < "$input_path"
