#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"

run_id=""
output=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" ]] || exit 2
[[ -n "$output" ]] || output="${APP_ROOT}/output/rsync_filter_preview_atlas.json"

compiled=$(cat "${APP_ROOT}/state/filter-compiled.json")
verdicts=$(echo "$compiled" | jq '[.path_verdicts[]] | sort_by(.transfer, .path)')
summary=$(echo "$verdicts" | jq '{include_count: ([.[] | select(.transfer=="include")] | length), exclude_count: ([.[] | select(.transfer=="exclude")] | length), candidate_delete_count: ([.[] | select(.delete_risk=="candidate")] | length)}')
jq -n --arg run_id "$run_id" --arg tree "$(echo "$compiled" | jq -r '.tree')" --argjson path_verdicts "$verdicts" --argjson rule_cascade "$(echo "$compiled" | jq '.rule_cascade')" --argjson summary "$summary" '{run_id: $run_id, tree: $tree, path_verdicts: $path_verdicts, rule_cascade: $rule_cascade, summary: $summary}' > "$output"
