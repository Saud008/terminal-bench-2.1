#!/usr/bin/env bash
set -euo pipefail

load_crush_bundle() {
  local map_dir="$1"
  local out="$2"
  local crush pool osd
  crush=$(cat "${map_dir}/crush_map.json")
  pool=$(cat "${map_dir}/pool.json")
  osd=$(cat "${map_dir}/osd_map.json")
  osd=$(echo "$osd" | jq '.osds |= map(. + {weight: (.reweight * 1024 | floor)})')
  jq -n --argjson crush "$crush" --argjson pool "$pool" --argjson osd "$osd" \
    --arg map_name "$(basename "$map_dir")" \
    '{crush: $crush, pool: $pool, osd: $osd, map_name: $map_name}' > "$out"
}
