#!/usr/bin/env bash
# Manifest emission — oracle LC_ALL=C path sort.

irfs_emit_manifest() {
  local output="$1"
  shift
  local -a rows=("$@")
  mkdir -p "$(dirname "${output}")"
  if [[ ${#rows[@]} -eq 0 ]]; then
    : > "${output}"
    return 0
  fi
  printf '%s\n' "${rows[@]}" | LC_ALL=C sort -t $'\t' -k1,1 > "${output}"
}
