#!/usr/bin/env bash
set -euo pipefail

UDEV_LIB="${UDEV_LIB:-/app/lib}"
# shellcheck source=../common.sh
source "${UDEV_LIB}/common.sh"
# shellcheck source=../bindio/inherit_attrs.sh
source "${UDEV_LIB}/bindio/inherit_attrs.sh"

compute_staging_digest() {
  local rules_json="$1"
  local devices_json="$2"
  local edges_json="$3"
  local inherited_map
  inherited_map="$(build_inherited_map "$devices_json")"
  local lines=""
  while IFS= read -r rule; do
    local rid pri tokens_part
    rid="$(jq -r '.rule_id' <<< "$rule")"
    pri="$(jq -r '.priority' <<< "$rule")"
    tokens_part="$(jq -r '.tokens | to_entries | sort_by(.key) | map(if (.value|type)=="array" then "\(.key)=\(.value|join(","))" else "\(.key)=\(.value)" end) | join(";")' <<< "$rule")"
    lines+="${rid};${pri};${tokens_part}"$'\n'
  done < <(jq -c '.[]' <<< "$rules_json")
  while IFS= read -r dev_id; do
    local attrs_part
    attrs_part="$(jq -r --arg id "$dev_id" --argjson m "$inherited_map" '.[$id] | to_entries | sort_by(.key) | map("\(.key)=\(.value)") | join(";")' <<< "$inherited_map")"
    lines+="${dev_id};${attrs_part}"$'\n'
  done < <(jq -r '.devices | sort_by(.dev_id) | .[].dev_id' <<< "$devices_json")
  while IFS= read -r edge; do
    local did rids
    did="$(jq -r '.dev_id' <<< "$edge")"
    rids="$(jq -r '.rule_ids | join(",")' <<< "$edge")"
    lines+="${did};${rids}"$'\n'
  done < <(jq -c 'sort_by(.dev_id) | .[]' <<< "$edges_json")
  sha256_lines "${lines%$'\n'}"
}

write_staging_snapshot() {
  local out="$1"
  local rules_json="$2"
  local devices_json="$3"
  local edges_json="$4"
  local digest
  digest="$(compute_staging_digest "$rules_json" "$devices_json" "$edges_json")"
  ensure_state_dir
  local prev_digest=""
  if [[ -f "$out" ]]; then
    prev_digest="$(jq -r '.staging_digest // ""' "$out" 2>/dev/null || true)"
  fi
  local seq
  seq="$(read_replay_seq)"
  if [[ "$digest" != "$prev_digest" ]]; then
    seq=$((seq + 1))
    write_replay_seq "$seq"
  fi
  jq -n \
    --argjson rules "$rules_json" \
    --argjson devices "$(jq -c '.devices' <<< "$devices_json")" \
    --argjson edges "$edges_json" \
    --arg digest "$digest" \
    '{schema_version:1,rules:$rules,devices:$devices,match_edges:$edges,staging_digest:$digest}' \
    | jq -S '.' > "$out"
}
