#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

config_dir="$1"
messages_path="$2"
seed="$3"
export_path="$4"
reload_mode="${5:-full}"

ensure_state_files

bash /app/lib/cache.sh "$config_dir" "$reload_mode" >/dev/null

filters="$(config_path "$config_dir" filters.conf)"
graph_cache="$(cache_file)"

processed=0
dropped=0
rewrite_applied=0

while IFS= read -r line; do
  [ -z "$line" ] && continue
  processed=$((processed + 1))

  rw_out="$(bash /app/lib/rewrite.sh "$line" "$config_dir")"
  msg_line="${rw_out%%|*}"
  rw_flag="${rw_out##*|}"
  if [ "$rw_flag" = "1" ]; then
    rewrite_applied=$((rewrite_applied + 1))
  fi

  gate="$(bash /app/lib/facility_gate.sh "$msg_line" "$config_dir")"
  if [ "$gate" = "drop" ]; then
    dropped=$((dropped + 1))
    continue
  fi

  while IFS='|' read -r route_id filter_id dest fallback dead; do
    [ -z "$route_id" ] && continue
    if bash /app/lib/boolean.sh "$msg_line" "$filters" "$filter_id"; then
      echo "${dest}" >> "$(deliveries_file)"
    fi
  done < "$graph_cache"
done < "$messages_path"

bash /app/lib/export.sh "$export_path" "$seed" "$config_dir" "$messages_path" \
  "$processed" "$dropped" "$rewrite_applied"

bash /app/lib/staging.sh "$seed" "$config_dir" "$messages_path" "$processed" \
  "$dropped" "$rewrite_applied" "$graph_cache"
