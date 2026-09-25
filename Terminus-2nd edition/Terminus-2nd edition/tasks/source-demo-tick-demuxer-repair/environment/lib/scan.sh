#!/usr/bin/env bash
# Discover demo files under a root directory.

sd_scan_dem_files() {
  local root="$1"
  local out_list="$2"
  : >"$out_list"
  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    printf '%s\t%s\n' "$(basename "$path")" "$path"
  done < <(find "$root" -type f -name '*.dem' | sort) | sort -t $'\t' -k1,1 | cut -f2- >"$out_list"
}
