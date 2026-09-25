#!/usr/bin/env bash
set -euo pipefail
inherit_device_attrs() {
  local devices_json="$1"
  local dev_id="$2"
  local merged='{}'
  local current="$dev_id"
  local guard=0
  while [[ -n "$current" && "$current" != "null" && $guard -lt 32 ]]; do
    local dev attrs parent
    dev="$(jq -c --arg id "$current" '.devices[] | select(.dev_id==$id)' <<< "$devices_json")"
    [[ -z "$dev" || "$dev" == "null" ]] && break
    attrs="$(jq -c '.attrs // {}' <<< "$dev")"
    merged="$(jq -c --argjson parent "$attrs" --argjson child "$merged" '$parent + $child' <<< '{}')"
    parent="$(jq -r '.parent_id // empty' <<< "$dev")"
    current="$parent"
    guard=$((guard + 1))
  done
  jq -c '.' <<< "$merged"
}

build_inherited_map() {
  local devices_json="$1"
  local result='{}'
  while IFS= read -r dev_id; do
    local attrs
    attrs="$(inherit_device_attrs "$devices_json" "$dev_id")"
    result="$(jq -c --arg id "$dev_id" --argjson a "$attrs" '. + {($id): $a}' <<< "$result")"
  done < <(jq -r '.devices[].dev_id' <<< "$devices_json")
  jq -c '.' <<< "$result"
}
