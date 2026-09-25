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
  local n
  n="$(jq '.devices | length' <<< "$devices_json")"
  sha256_lines "device_count=${n}"
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
