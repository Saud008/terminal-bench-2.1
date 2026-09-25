#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/ap91/pin/pin_match.sh"
source "${APP_ROOT}/internal/ap91/version/version_compare.sh"
source "${APP_ROOT}/internal/ap91/arch/arch_filter.sh"

run_id=""
output=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" && -n "$output" ]] || exit 2

snap=$(cat "${APP_ROOT}/state/aptpol-staging.json")
arch=$(echo "$snap" | jq -r '.target_arch')
prefs=$(echo "$snap" | jq -c '.preferences')
packages=$(echo "$snap" | jq -c '.packages')
queries=$(echo "$snap" | jq -c '.queries')

candidates="[]"
while IFS= read -r q; do
  [[ -z "$q" ]] && continue
  pkg=$(echo "$q" | jq -r '.package')
  best=""
  best_prio=-1
  best_src=""
  while IFS= read -r cand; do
    [[ -z "$cand" ]] && continue
    name=$(echo "$cand" | jq -r '.package')
    [[ "$name" != "$pkg" ]] && continue
    carch=$(echo "$cand" | jq -r '.arch // ""')
    arch_ok "$carch" "$arch" || continue
    ver=$(echo "$cand" | jq -r '.version')
    prio=$(pin_priority_for_pkg "$prefs" "$pkg" "$ver")
    src=$(echo "$cand" | jq -r '.source_id')
    if (( prio > best_prio )); then
      best="$ver"
      best_prio=$prio
      best_src="$src"
    elif (( prio == best_prio )) && [[ -n "$best" ]]; then
      if version_gt "$ver" "$best"; then
        best="$ver"
        best_src="$src"
      fi
    fi
  done < <(echo "$packages" | jq -c '.[]')

  if [[ -z "$best" ]]; then
    candidates=$(echo "$candidates" | jq --arg p "$pkg" \
      '. + [{package: $p, selected_version: null, source_id: null, pin_priority: 0, reason: "no_candidate"}]')
  else
    candidates=$(echo "$candidates" | jq --arg p "$pkg" --arg v "$best" --arg s "$best_src" --argjson pr "$best_prio" \
      '. + [{package: $p, selected_version: $v, source_id: $s, pin_priority: $pr, reason: "pin_and_version"}]')
  fi
done < <(echo "$queries" | jq -c '.[]')

candidates=$(echo "$candidates" | jq 'sort_by(.package)')
audit=$(echo "$candidates" | jq -c '.' | sha256sum | awk '{print $1}')
jq -n --arg run_id "$run_id" --argjson candidates "$candidates" --arg audit "$audit" \
  '{run_id: $run_id, candidates: $candidates, summary: {query_count: ($candidates|length)}, audit_digest: $audit}' \
  > "$output"
