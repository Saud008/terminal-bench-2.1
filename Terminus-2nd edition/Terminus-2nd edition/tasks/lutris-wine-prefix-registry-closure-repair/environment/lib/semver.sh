#!/usr/bin/env bash
# DXVK semver pin check.

semver_pin_satisfied() {
  local version="$1"
  local pin="$2"
  local req="${pin#>=}"
  if [[ "$version" > "$req" || "$version" == "$req" ]]; then
    return 0
  fi
  return 1
}
