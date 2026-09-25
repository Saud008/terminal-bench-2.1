#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

export_path="$1"
seed="$2"
config_dir="$3"
messages_path="$4"
processed="$5"
dropped="$6"
rewrite_applied="$7"

declare -A counts
while IFS= read -r dest; do
  [ -z "$dest" ] && continue
  counts["$dest"]=$(( ${counts["$dest"]:-0} + 1 ))
done < "$(deliveries_file)"

total=0
for dest in "${!counts[@]}"; do
  total=$((total + counts[$dest]))
done

{
  printf '{'
  printf '"seed":"%s",' "$seed"
  printf '"config_dir":"%s",' "$config_dir"
  printf '"messages_path":"%s",' "$messages_path"
  printf '"total_messages":%s,' "$processed"
  printf '"dropped_at_facility_gate":%s,' "$dropped"
  printf '"total_deliveries":%s,' "$total"
  printf '"rewrite_applied":%s,' "$rewrite_applied"
  printf '"deliveries":['
  first=1
  for dest in $(printf '%s\n' "${!counts[@]}" | sort); do
    [ "$first" -eq 1 ] || printf ','
    first=0
    printf '{"destination":"%s","count":%s}' "$dest" "${counts[$dest]}"
  done
  printf ']}'
} > "$export_path"
