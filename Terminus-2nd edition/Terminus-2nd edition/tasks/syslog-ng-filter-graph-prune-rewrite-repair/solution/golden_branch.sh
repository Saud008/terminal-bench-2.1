#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

config_dir="$1"
input_path="$2"
output_path="$3"

: > "$output_path"
while IFS='|' read -r route_id filter_id dest fallback dead; do
  [ -z "$route_id" ] && continue
  echo "${route_id}|${filter_id}|${dest}|${fallback}|${dead}" >> "$output_path"
done < "$input_path"
