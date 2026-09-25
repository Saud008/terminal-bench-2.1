#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

seed="$1"
config_dir="$2"
messages_path="$3"
processed="$4"
dropped="$5"
rewrite_applied="$6"
graph_cache="$7"

config_hash="$(cat "$(hash_file)")"
routes="["
first=1
while IFS='|' read -r route_id _ _ _ _; do
  [ -z "$route_id" ] && continue
  [ "$first" -eq 1 ] || routes+=","
  first=0
  routes+="\"${route_id}\""
done < "$graph_cache"
routes+="]"

{
  printf '{'
  printf '"seed":"%s",' "$seed"
  printf '"config_dir":"%s",' "$config_dir"
  printf '"messages_path":"%s",' "$messages_path"
  printf '"processed_messages":%s,' "$processed"
  printf '"dropped_at_facility_gate":%s,' "$dropped"
  printf '"rewrite_applied":%s,' "$rewrite_applied"
  printf '"config_hash":"%s",' "$config_hash"
  printf '"active_routes":%s' "$routes"
  printf '}'
} > "$(snapshot_file)"
