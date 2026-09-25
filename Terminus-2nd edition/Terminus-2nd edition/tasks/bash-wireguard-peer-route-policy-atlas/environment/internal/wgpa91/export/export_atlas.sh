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
[[ -n "$run_id" && -n "$output" ]] || exit 2

snap=$(cat "${APP_ROOT}/state/wgpatlas-workspace.json")

peers=$(echo "$snap" | jq 'sort_by(.peer_id) | [.[] | {public_key, peer_id, interface, allowed_ips, endpoint, disabled}]')
overlaps=$(echo "$snap" | jq '.overlaps')
route_conflicts=$(echo "$snap" | jq '.route_conflicts')
active_count=$(echo "$peers" | jq '[.[] | select(.disabled == false)] | length')
audit=$(echo "$peers" | jq -c '.' | sha256sum | awk '{print $1}')
jq -n --arg run_id "$run_id" --argjson peers "$peers" --argjson overlaps "$overlaps" --argjson route_conflicts "$route_conflicts" --argjson active_count "$active_count" --arg audit "$audit" '{run_id: $run_id, peers: $peers, overlaps: $overlaps, route_conflicts: $route_conflicts, summary: {active_peer_count: $active_count, overlap_count: ($overlaps|length), conflict_count: ($route_conflicts|length)}, audit_digest: $audit}' > "$output"
