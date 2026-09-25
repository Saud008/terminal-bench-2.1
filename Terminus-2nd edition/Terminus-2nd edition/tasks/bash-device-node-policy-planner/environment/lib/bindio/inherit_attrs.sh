#!/usr/bin/env bash
set -euo pipefail

inherit_device_attrs() {
  local devices_json="$1"
  local dev_id="$2"
  jq -c --arg id "$dev_id" '.devices[] | select(.dev_id==$id) | .attrs // {}' <<< "$devices_json"
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
