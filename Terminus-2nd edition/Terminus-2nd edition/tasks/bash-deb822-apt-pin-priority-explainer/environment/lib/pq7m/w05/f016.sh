#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/lib/pq7m/w03/f012.sh"
source "${APP_ROOT}/lib/pq7m/w03/f013.sh"
source "${APP_ROOT}/lib/pq7m/w04/f014.sh"

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

graph=$(cat "${APP_ROOT}/state/deb822-policy-graph.json")
arch=$(echo "$graph" | jq -r '.target_arch')
prefs=$(echo "$graph" | jq -c '.preferences')
rows=$(echo "$graph" | jq -c '.package_rows')
queries=$(echo "$graph" | jq -c '.queries')

install_rows="[]"
while IFS= read -r q; do
  [[ -z "$q" ]] && continue
  pkg=$(echo "$q" | jq -r '.package')
  best=""
  best_prio=-1
  best_origin=""
  while IFS= read -r cand; do
    [[ -z "$cand" ]] && continue
    name=$(echo "$cand" | jq -r '.package')
    [[ "$name" != "$pkg" ]] && continue
    carch=$(echo "$cand" | jq -r '.arch // ""')
    cpu_arch_allowed "$carch" "$arch" || continue
    ver=$(echo "$cand" | jq -r '.version')
    prio=$(effective_pin "$prefs" "$pkg" "$ver")
    oid=$(echo "$cand" | jq -r '.origin_id')
    if (( prio > best_prio )); then
      best="$ver"
      best_prio=$prio
      best_origin="$oid"
    elif (( prio == best_prio )) && [[ -n "$best" ]]; then
      # Baseline keeps first candidate on priority tie.
      :
    fi
  done < <(echo "$rows" | jq -c '.[]')

  if [[ -z "$best" ]]; then
    install_rows=$(echo "$install_rows" | jq --arg p "$pkg" \
      '. + [{package: $p, chosen_version: null, origin_id: null, effective_priority: 0, verdict: "none"}]')
  else
    install_rows=$(echo "$install_rows" | jq --arg p "$pkg" --arg v "$best" --arg o "$best_origin" --argjson pr "$best_prio" \
      '. + [{package: $p, chosen_version: $v, origin_id: $o, effective_priority: $pr, verdict: "selected"}]')
  fi
done < <(echo "$queries" | jq -c '.[]')

install_rows=$(echo "$install_rows" | jq 'sort_by(.package)')
audit=$(echo "$install_rows" | jq -c '.' | sha256sum | awk '{print $1}')
jq -n --arg run_id "$run_id" --argjson install_rows "$install_rows" --arg audit "$audit" \
  '{run_id: $run_id, install_candidates: $install_rows, totals: {queries: ($install_rows|length)}, audit_digest: $audit}' \
  > "$output"
