#!/usr/bin/env bash
# Discover demo files under a root directory.

sd_scan_dem_files() {
  local root="$1"
  local out_list="$2"
  find "$root" -type f -name '*.dem' | while IFS= read -r path; do
    rel="${path#"${root%/}"/}"
    rel="${rel//\\//}"
    printf '%s\t%s\n' "$rel" "$path"
  done | LC_ALL=C sort -t $'\t' -k1,1 | cut -f2- >"$out_list"
}
