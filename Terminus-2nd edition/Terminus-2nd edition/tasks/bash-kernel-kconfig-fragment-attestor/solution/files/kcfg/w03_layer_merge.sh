#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../p01.sh"
source "$(dirname "${BASH_SOURCE[0]}")/../p02.sh"

merge_layers() {
  local defconfig="$1"
  local frag_dir="$2"
  local merged="{}"
  merged=$(parse_kconfig_file "$defconfig")
  while IFS= read -r frag; do
    [[ -z "$frag" ]] && continue
    layer=$(parse_kconfig_file "${frag_dir}/${frag}")
    merged=$(jq -n --argjson base "$merged" --argjson layer "$layer" '$base + $layer')
  done < <(list_fragments_ordered "$frag_dir")
  echo "$merged"
}
