#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

config_dir="$1"
output_path="$2"

filters="$(config_path "$config_dir" filters.conf)"
graph="$(config_path "$config_dir" graph.conf)"

: > "$output_path"
while IFS='|' read -r route_id filter_id dest fallback dead; do
  [ -z "$route_id" ] && continue
  if ! grep -q "^${filter_id}|" "$filters"; then
    continue
  fi
  if [ "$dead" = "1" ]; then
    continue
  fi
  echo "${route_id}|${filter_id}|${dest}|${fallback}|${dead}" >> "$output_path"
done < "$graph"
