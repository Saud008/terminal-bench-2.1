#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"

tree=""
run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tree) tree="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$tree" && -n "$run_id" ]] || exit 2

root="${TB3_TREE_ROOT:-${APP_ROOT}/fixtures/trees}"
manifest="${root}/${tree}/manifest.json"
[[ -f "$manifest" ]] || exit 3

data=$(cat "$manifest")
sender=$(echo "$data" | jq -c '.sender_paths')
receiver=$(echo "$data" | jq -c '.receiver_paths')
root_rules=$(echo "$data" | jq -c '.root_rules')
cascade_overlays=$(echo "$data" | jq -c '.cascade_overlays')

sender=$(echo "$sender" | jq '[.[] | select(contains(".cache") | not)]')

mkdir -p "${APP_ROOT}/work"
jq -n --arg tree "$tree" --arg run_id "$run_id" --argjson sender "$sender" \
  --argjson receiver "$receiver" --argjson root_rules "$root_rules" --argjson cascade_overlays "$cascade_overlays" \
  '{tree: $tree, run_id: $run_id, sender_paths: $sender, receiver_paths: $receiver, root_rules: $root_rules, cascade_overlays: $cascade_overlays}' \
  > "${APP_ROOT}/work/${run_id}-inventory.json"
