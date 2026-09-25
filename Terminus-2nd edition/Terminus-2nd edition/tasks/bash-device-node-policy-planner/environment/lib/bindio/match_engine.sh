#!/usr/bin/env bash
# Match devices to ordered rules
set -euo pipefail

UDEV_LIB="${UDEV_LIB:-/app/lib}"
# shellcheck source=../common.sh
source "${UDEV_LIB}/common.sh"
# shellcheck source=inherit_attrs.sh
source "${UDEV_LIB}/bindio/inherit_attrs.sh"
# shellcheck source=bind_tsv.sh
source "${UDEV_LIB}/bindio/bind_tsv.sh"

rule_matches_device() {
  local rule_json="$1"
  local device_json="$2"
  local inherited_attrs="$3"
  local catalog_json="$4"
  local subsystem kernel modalias
  subsystem="$(jq -r '.subsystem // ""' <<< "$device_json")"
  kernel="$(jq -r '.kernel // ""' <<< "$device_json")"
  modalias="$(jq -r '.modalias // ""' <<< "$device_json")"
  local tokens
  tokens="$(jq -c '.tokens' <<< "$rule_json")"
  local sub_t kern_t
  sub_t="$(jq -r '.SUBSYSTEM // ""' <<< "$tokens")"
  kern_t="$(jq -r '.KERNEL // ""' <<< "$tokens")"
  if [[ -n "$sub_t" && "$sub_t" != "$subsystem" ]]; then
    return 1
  fi
  if [[ -n "$kern_t" ]]; then
    glob_match "$kern_t" "$kernel" || return 1
  fi
  while IFS= read -r attr_line; do
    [[ -z "$attr_line" ]] && continue
    local an="${attr_line%%=*}"
    local av="${attr_line#*=}"
    local dv
    dv="$(jq -r --arg k "${an#ATTR:}" '.[$k] // ""' <<< "$inherited_attrs")"
    [[ "$dv" == "$av" ]] || return 1
  done < <(jq -r '.tokens | to_entries[] | select(.key|startswith("ATTR:")) | "\(.key)=\(.value)"' <<< "$rule_json")
  local mod_t
  mod_t="$(jq -r '.MODALIAS // ""' <<< "$tokens")"
  if [[ -n "$mod_t" ]]; then
    modalias_rule_matches "$modalias" "$mod_t" "$catalog_json" || return 1
  fi
  return 0
}

build_match_edges() {
  local rules_json="$1"
  local devices_json="$2"
  local catalog_json="$3"
  local inherited_map
  inherited_map="$(build_inherited_map "$devices_json")"
  local edges='[]'
  while IFS= read -r dev; do
    local dev_id attrs dev_obj rule_ids='[]'
    dev_id="$(jq -r '.dev_id' <<< "$dev")"
    dev_obj="$dev"
    attrs="$(jq -c --arg id "$dev_id" '.[$id]' <<< "$inherited_map")"
    while IFS= read -r rule; do
      if rule_matches_device "$rule" "$dev_obj" "$attrs" "$catalog_json"; then
        local rid
        rid="$(jq -r '.rule_id' <<< "$rule")"
        rule_ids="$(jq -c --arg r "$rid" '. + [$r]' <<< "$rule_ids")"
      fi
    done < <(jq -c '.[]' <<< "$rules_json")
    edges="$(jq -c --arg id "$dev_id" --argjson r "$rule_ids" '. + [{dev_id:$id,rule_ids:$r}]' <<< "$edges")"
  done < <(jq -c '.devices[]' <<< "$devices_json")
  jq -c '.' <<< "$edges"
}
