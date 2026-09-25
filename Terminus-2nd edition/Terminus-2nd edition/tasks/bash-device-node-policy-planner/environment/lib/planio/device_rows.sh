#!/usr/bin/env bash
set -euo pipefail

UDEV_LIB="${UDEV_LIB:-/app/lib}"
# shellcheck source=../common.sh
source "${UDEV_LIB}/common.sh"
# shellcheck source=../ruleio/parse_rules.sh
source "${UDEV_LIB}/ruleio/parse_rules.sh"
# shellcheck source=../ruleio/order_rules.sh
source "${UDEV_LIB}/ruleio/order_rules.sh"
# shellcheck source=../bindio/match_engine.sh
source "${UDEV_LIB}/bindio/match_engine.sh"
# shellcheck source=alias_arb.sh
source "${UDEV_LIB}/planio/alias_arb.sh"
# shellcheck source=owner_lane.sh
source "${UDEV_LIB}/planio/owner_lane.sh"

compute_plan_digest() {
  local devices_plan="$1"
  local lines=""
  while IFS= read -r row; do
    lines+="${row}"$'\n'
  done < <(jq -r 'sort_by(.dev_id)[] | [.dev_id, (.symlinks|join(",")), .owner, .group, .mode, (.winning_rules|join(","))] | join("|")' <<< "$devices_plan")
  sha256_lines "${lines%$'\n'}"
}

export_device_plan() {
  local staging="$1"
  local policy_file="$2"
  local out="$3"
  local rules_dir="${UDEVPLAN_RULES_DIR:-/app/fixtures/rules}"
  local devices_file="${UDEVPLAN_DEVICES:-/app/fixtures/devices.json}"
  local modalias_file="${UDEVPLAN_MODALIAS:-/app/fixtures/modalias.tsv}"
  local rules devices_json catalog edges
  rules="$(order_rules "$(parse_rules_dir "$rules_dir")")"
  devices_json="$(cat "$devices_file")"
  catalog="$(load_modalias_catalog "$modalias_file")"
  edges="$(build_match_edges "$rules" "$devices_json" "$catalog")"
  local policy
  policy="$(cat "$policy_file")"
  local rules_by_id
  rules_by_id="$(jq -c 'reduce .[] as $r ({}; .[$r.rule_id]=$r)' <<< "$rules")"
  local plan_devices='[]'
  local all_collisions='[]'
  while IFS= read -r edge; do
    local dev_id rule_ids
    dev_id="$(jq -r '.dev_id' <<< "$edge")"
    rule_ids="$(jq -c '.rule_ids' <<< "$edge")"
    local sym perm slink_json
    slink_json="$(resolve_symlinks_for_device "$rule_ids" "$rules_by_id")"
    perm="$(resolve_permissions "$rule_ids" "$rules_by_id" "$policy")"
    local symlinks collisions
    symlinks="$(jq -c '.symlinks' <<< "$slink_json")"
    collisions="$(jq -c '.collisions' <<< "$slink_json")"
    all_collisions="$(jq -c --argjson c "$collisions" '. + $c' <<< "$all_collisions")"
    plan_devices="$(jq -c \
      --arg id "$dev_id" \
      --argjson sl "$symlinks" \
      --arg o "$(jq -r '.owner' <<< "$perm")" \
      --arg g "$(jq -r '.group' <<< "$perm")" \
      --arg m "$(jq -r '.mode' <<< "$perm")" \
      --argjson wr "$rule_ids" \
      '. + [{dev_id:$id,symlinks:$sl,owner:$o,group:$g,mode:$m,winning_rules:$wr}]' <<< "$plan_devices")"
  done < <(jq -c '.[]' <<< "$edges")
  local digest
  digest="$(compute_plan_digest "$plan_devices")"
  ensure_state_dir
  jq -n \
    --argjson devs "$(jq -c 'sort_by(.dev_id)' <<< "$plan_devices")" \
    --argjson coll "$(jq -c 'sort_by(.symlink)' <<< "$all_collisions")" \
    --arg digest "$digest" \
    '{schema_version:1,devices:$devs,collisions:$coll,plan_digest:$digest}' \
    | jq -S '.' > "$out"
}
