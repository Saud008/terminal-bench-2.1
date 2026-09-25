#!/usr/bin/env bash
set -euo pipefail

_emit_rule_symlinks() {
  local rule_json="$1"
  jq -r '.tokens.SYMLINK | if type == "array" then .[] elif type == "string" then . else empty end' <<< "$rule_json"
}

resolve_symlinks_for_device() {
  local rule_ids_json="$1"
  local rules_by_id="$2"
  local symlinks='[]'
  local collisions='[]'
  local seen='{}'
  while IFS= read -r rid; do
    [[ -z "$rid" ]] && continue
    local rule
    rule="$(jq -c --arg r "$rid" '.[$r]' <<< "$rules_by_id")"
    while IFS= read -r sl; do
      [[ -z "$sl" ]] && continue
      if jq -e --arg s "$sl" 'has($s)' <<< "$seen" >/dev/null; then
        collisions="$(jq -c --arg s "$sl" --arg w "$rid" \
          '. + [{symlink:$s,candidates:[$w],winner:$w}]' <<< "$collisions")"
      else
        seen="$(jq -c --arg s "$sl" --arg w "$rid" '. + {($s): $w}' <<< "$seen")"
        symlinks="$(jq -c --arg s "$sl" '. + [$s]' <<< "$symlinks")"
      fi
    done < <(_emit_rule_symlinks "$rule")
  done < <(jq -r '.[]' <<< "$rule_ids_json")
  jq -n --argjson s "$(jq -c 'sort' <<< "$symlinks")" --argjson c "$collisions" '{symlinks:$s,collisions:$c}'
}
