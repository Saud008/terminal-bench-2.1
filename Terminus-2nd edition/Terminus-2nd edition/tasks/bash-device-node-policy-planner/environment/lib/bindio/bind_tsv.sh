#!/usr/bin/env bash
set -euo pipefail

UDEV_LIB="${UDEV_LIB:-/app/lib}"
# shellcheck source=../common.sh
source "${UDEV_LIB}/common.sh"

load_modalias_catalog() {
  local path="$1"
  local obj='{}'
  if [[ ! -f "$path" ]]; then
    jq -c '.' <<< "$obj"
    return 0
  fi
  while IFS=$'\t' read -r pattern tag || [[ -n "$pattern" ]]; do
    [[ -z "$pattern" ]] && continue
    obj="$(jq -c --arg p "$pattern" --arg t "$tag" '. + {($p): $t}' <<< "$obj")"
  done < "$path"
  jq -c '.' <<< "$obj"
}

modalias_rule_matches() {
  local device_modalias="$1"
  local rule_pattern="$2"
  local catalog_json="$3"
  [[ "$device_modalias" == "$rule_pattern" ]]
}
