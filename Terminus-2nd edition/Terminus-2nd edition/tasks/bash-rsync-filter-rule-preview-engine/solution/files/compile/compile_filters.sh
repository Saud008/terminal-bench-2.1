#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/rsfp93/rules/parse_filters.sh"
source "${APP_ROOT}/internal/rsfp93/rules/match_rule.sh"
source "${APP_ROOT}/internal/rsfp93/cascade/cascade_stack.sh"
source "${APP_ROOT}/internal/rsfp93/prune/prune_walk.sh"
source "${APP_ROOT}/internal/rsfp93/delete/delete_risk.sh"

run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" ]] || exit 2

inv="${APP_ROOT}/work/${run_id}-inventory.json"
data=$(cat "$inv")
sender=$(echo "$data" | jq -c '.sender_paths')
receiver=$(echo "$data" | jq -c '.receiver_paths')
root_rules=$(echo "$data" | jq -c '.root_rules')
cascade_overlays=$(echo "$data" | jq -c '.cascade_overlays')

path_verdicts="[]"
rule_cascade="[]"
while IFS= read -r p; do
  [[ -z "$p" ]] && continue
  cascaded=$(cascaded_rules_for_path "$p" "$root_rules" "$cascade_overlays")
  cascaded_rules=$(echo "$cascaded" | jq -c '.rules')
  cascade_depth=$(echo "$cascaded" | jq -r '.cascade_depth')
  rule_cascade=$(echo "$rule_cascade" | jq --arg p "$p" --argjson c "$(echo "$cascaded" | jq -c '.rule_cascade')" '. + [{path: $p, cascade: $c}]')

  parsed=$(parse_rule_list "$cascaded_rules")
  matched=$(match_rule_for_path "$p" "$parsed")
  transfer=$(echo "$matched" | jq -r '.transfer')
  token=$(echo "$matched" | jq -r '.token')
  idx=$(echo "$matched" | jq -r '.matched_rule_index')
  if ! echo "$sender" | jq -e --arg p "$p" '.[] | select(. == $p)' >/dev/null; then
    transfer="exclude"
  fi
  prune=$(should_prune_directory "$p" "$transfer" "$token")
  risk=$(classify_delete_risk "$p" "$transfer" "$parsed" "$receiver" "$sender")
  path_verdicts=$(echo "$path_verdicts" | jq --arg p "$p" --arg tr "$transfer" --arg dr "$risk" --argjson md "$cascade_depth" --argjson idx "$idx" --argjson prune "$prune" '. + [{path: $p, transfer: $tr, delete_risk: $dr, cascade_depth: $md, matched_rule_index: $idx, prune: $prune}]')
done < <(jq -r '.sender_paths[], .receiver_paths[]' <<<"$data" | sort -u)

path_verdicts=$(echo "$path_verdicts" | jq 'sort_by(.path)')

mkdir -p "${APP_ROOT}/state"
jq -n --arg run_id "$run_id" --arg tree "$(echo "$data" | jq -r '.tree')" --argjson receiver "$receiver" --argjson path_verdicts "$path_verdicts" --argjson rule_cascade "$rule_cascade" \
  '{run_id: $run_id, tree: $tree, receiver_paths: $receiver, path_verdicts: $path_verdicts, rule_cascade: $rule_cascade}' \
  > "${APP_ROOT}/state/filter-compiled.json"
