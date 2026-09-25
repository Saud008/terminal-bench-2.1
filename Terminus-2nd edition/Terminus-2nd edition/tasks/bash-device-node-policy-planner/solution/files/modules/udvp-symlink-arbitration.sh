#!/usr/bin/env bash
set -euo pipefail

#!/usr/bin/env
_emit_rule_symlinks() {
  local rule_json="$1"
  jq -r '.tokens.SYMLINK | if type == "array" then .[] elif type == "string" then . else empty end' <<< "$rule_json"
}

resolve_symlinks_for_device() {
  local rule_ids_json="$1"
  local rules_by_id="$2"
  declare -A symlink_to_rules=()
  declare -A symlink_winner=()
  while IFS= read -r rid; do
    [[ -z "$rid" ]] && continue
    local rule
    rule="$(jq -c --arg r "$rid" '.[$r]' <<< "$rules_by_id")"
    while IFS= read -r sl; do
      [[ -z "$sl" ]] && continue
      if [[ -z "${symlink_to_rules[$sl]+x}" ]]; then
        symlink_to_rules[$sl]="$rid"
      else
        symlink_to_rules[$sl]="${symlink_to_rules[$sl]},$rid"
      fi
      symlink_winner[$sl]="$rid"
    done < <(_emit_rule_symlinks "$rule")
  done < <(jq -r '.[]' <<< "$rule_ids_json")
  local symlinks='[]'
  local collisions='[]'
  for sl in "${!symlink_winner[@]}"; do
    symlinks="$(jq -c --arg s "$sl" '. + [$s]' <<< "$symlinks")"
    local cands="${symlink_to_rules[$sl]}"
    IFS=',' read -ra arr <<< "$cands"
    if [[ ${#arr[@]} -gt 1 ]]; then
      local winner="${symlink_winner[$sl]}"
      collisions="$(jq -c --arg s "$sl" --arg w "$winner" --argjson c "$(printf '%s\n' "${arr[@]}" | jq -R . | jq -s .)" \
        '. + [{symlink:$s,candidates:$c,winner:$w}]' <<< "$collisions")"
    fi
  done
  jq -n --argjson s "$(jq -c 'sort' <<< "$symlinks")" --argjson c "$collisions" '{symlinks:$s,collisions:$c}'
}
