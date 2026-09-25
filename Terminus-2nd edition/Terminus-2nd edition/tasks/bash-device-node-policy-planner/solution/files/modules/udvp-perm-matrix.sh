#!/usr/bin/env bash
set -euo pipefail

resolve_permissions() {
  local rule_ids_json="$1"
  local rules_by_id="$2"
  local policy_json="$3"
  local owner="" group="" mode=""
  local rev
  rev="$(jq -c 'reverse' <<< "$rule_ids_json")"
  while IFS= read -r rid; do
    [[ -z "$rid" ]] && continue
    local rule t
    rule="$(jq -c --arg r "$rid" '.[$r]' <<< "$rules_by_id")"
    t="$(jq -r '.tokens.OWNER // empty' <<< "$rule")"
    [[ -n "$t" && -z "$owner" ]] && owner="$t"
    t="$(jq -r '.tokens.GROUP // empty' <<< "$rule")"
    [[ -n "$t" && -z "$group" ]] && group="$t"
    t="$(jq -r '.tokens.MODE // empty' <<< "$rule")"
    [[ -n "$t" && -z "$mode" ]] && mode="$t"
  done < <(jq -r '.[]' <<< "$rev")
  [[ -z "$owner" ]] && owner="$(jq -r '.default_owner // "root"' <<< "$policy_json")"
  [[ -z "$group" ]] && group="$(jq -r '.default_group // "root"' <<< "$policy_json")"
  [[ -z "$mode" ]] && mode="$(jq -r '.default_mode // "0644"' <<< "$policy_json")"
  mode="$(printf '%04o' "$((8#$mode))")"
  jq -n --arg o "$owner" --arg g "$group" --arg m "$mode" '{owner:$o,group:$g,mode:$m}'
}
