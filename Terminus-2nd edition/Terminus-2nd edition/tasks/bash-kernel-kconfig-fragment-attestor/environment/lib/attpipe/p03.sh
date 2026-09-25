#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/p01.sh"

merge_layers() {
  local defconfig="$1"
  local frag_dir="$2"
  local merged="{}"
  while IFS= read -r frag; do
    [[ -z "$frag" ]] && continue
    layer=$(parse_kconfig_file "${frag_dir}/${frag}")
    merged=$(jq -n --argjson base "$merged" --argjson layer "$layer" '$base + $layer')
  done < <(find "$frag_dir" -maxdepth 1 -type f -name '*.fragment' -printf '%f\n' | sort -r)
  base=$(parse_kconfig_file "$defconfig")
  jq -n --argjson base "$base" --argjson merged "$merged" '$merged + $base'
}
