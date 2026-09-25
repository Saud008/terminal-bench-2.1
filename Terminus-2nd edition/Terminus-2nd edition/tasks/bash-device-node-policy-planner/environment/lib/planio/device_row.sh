#!/usr/bin/env bash
set -euo pipefail
UDEV_LIB="${UDEV_LIB:-/app/lib}"
# shellcheck source=alias_arb.sh
source "${UDEV_LIB}/planio/alias_arb.sh"
# shellcheck source=owner_lane.sh
source "${UDEV_LIB}/planio/owner_lane.sh"

build_device_row() {
  local dev_id="$1"
  local rule_ids_json="$2"
  local rules_by_id="$3"
  local policy_json="$4"
  local slink_json perm
  slink_json="$(resolve_symlinks_for_device "$rule_ids_json" "$rules_by_id")"
  perm="$(resolve_permissions "$rule_ids_json" "$rules_by_id" "$policy_json")"
  jq -n \
    --arg id "$dev_id" \
    --argjson sl "$(jq -c '.symlinks' <<< "$slink_json")" \
    --arg o "$(jq -r '.owner' <<< "$perm")" \
    --arg g "$(jq -r '.group' <<< "$perm")" \
    --arg m "$(jq -r '.mode' <<< "$perm")" \
    --argjson wr "$rule_ids_json" \
    '{dev_id:$id,symlinks:$sl,owner:$o,group:$g,mode:$m,winning_rules:$wr}'
}
