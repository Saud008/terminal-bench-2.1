#!/usr/bin/env bash
# Manifest emission — broken baseline sorts by size not path.

# shellcheck source=/app/lib/decoy/irfs_sort_legacy.sh
source "${ROOT:-/app}/lib/decoy/irfs_sort_legacy.sh"

irfs_emit_manifest() {
  local output="$1"
  shift
  local -a rows=("$@")
  mkdir -p "$(dirname "${output}")"
  if [[ ${#rows[@]} -eq 0 ]]; then
    : > "${output}"
    return 0
  fi
  # baseline: legacy size sort instead of path sort
  printf '%s\n' "${rows[@]}" | irfs_legacy_sort_rows > "${output}"
}
