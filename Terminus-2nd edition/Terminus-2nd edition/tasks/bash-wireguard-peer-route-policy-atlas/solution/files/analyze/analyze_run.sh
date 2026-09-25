#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/wgpa91/cidr/cidr_overlap.sh"
source "${APP_ROOT}/internal/wgpa91/endpoint/endpoint_rank.sh"
source "${APP_ROOT}/internal/wgpa91/routes/route_conflict.sh"
source "${APP_ROOT}/internal/wgpa91/policy/disabled_peer.sh"
source "${APP_ROOT}/internal/wgpa91/workspace/workspace_fingerprint.sh"

run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" ]] || exit 2

ingest="${APP_ROOT}/work/${run_id}-ingest.json"
data=$(cat "$ingest")
policy=$(echo "$data" | jq -c '.policy')
site=$(echo "$data" | jq -r '.site')

peers="[]"
while IFS= read -r cfg; do
  [[ -z "$cfg" ]] && continue
  iface=$(echo "$cfg" | jq -r '.interface')
  while IFS= read -r peer; do
    [[ -z "$peer" ]] && continue
    pk=$(echo "$peer" | jq -r '.PublicKey')
    name=$(echo "$peer" | jq -r '.Name // .PublicKey')
    if is_peer_disabled "$name" "$policy"; then
      continue
    fi
    allowed=$(echo "$peer" | jq -c '.AllowedIPs // []')
    endpoint=$(pick_endpoint "$name" "$policy")
    [[ -z "$endpoint" ]] && endpoint=$(echo "$peer" | jq -r '.Endpoint // ""')
    peers=$(echo "$peers" | jq --arg pk "$pk" --arg name "$name" --arg iface "$iface" \
      --argjson allowed "$allowed" --arg endpoint "$endpoint" \
      '. + [{public_key: $pk, peer_id: $name, interface: $iface, allowed_ips: $allowed, endpoint: $endpoint, disabled: false}]')
  done < <(echo "$cfg" | jq -c '.peers[]')
done < <(echo "$data" | jq -c '.configs[]')

overlaps="[]"
while IFS= read -r p1; do
  [[ -z "$p1" ]] && continue
  id1=$(echo "$p1" | jq -r '.peer_id')
  while IFS= read -r c1; do
    [[ -z "$c1" ]] && continue
    while IFS= read -r p2; do
      [[ -z "$p2" ]] && continue
      id2=$(echo "$p2" | jq -r '.peer_id')
      [[ "$id1" > "$id2" || "$id1" == "$id2" ]] && continue
      while IFS= read -r c2; do
        [[ -z "$c2" ]] && continue
        if cidrs_overlap "$c1" "$c2"; then
          overlaps=$(echo "$overlaps" | jq --arg a "$id1" --arg b "$id2" --arg c1 "$c1" --arg c2 "$c2" \
            '. + [{peer_a: $a, peer_b: $b, cidr_a: $c1, cidr_b: $c2, reason: "allowed_ip_overlap"}]')
        fi
      done < <(echo "$p2" | jq -r '.allowed_ips[]?')
    done < <(echo "$peers" | jq -c '.[]')
  done < <(echo "$p1" | jq -r '.allowed_ips[]?')
done < <(echo "$peers" | jq -c '.[]')

route_conflicts=$(detect_route_conflicts "$(echo "$data" | jq -c '.routes')")
overlaps=$(echo "$overlaps" | jq 'sort_by(.peer_a, .peer_b, .cidr_a, .cidr_b)')
disabled_skipped=$(echo "$policy" | jq -c '.disabled_peers // []')

body=$(jq -n \
  --arg run_id "$run_id" \
  --arg site "$site" \
  --argjson peers "$peers" \
  --argjson overlaps "$overlaps" \
  --argjson route_conflicts "$route_conflicts" \
  --argjson disabled_skipped "$disabled_skipped" \
  '{run_id: $run_id, site: $site, peers: $peers, overlaps: $overlaps, route_conflicts: $route_conflicts, disabled_skipped: $disabled_skipped}')
fp=$(workspace_fingerprint "$body")
echo "$body" | jq --arg fp "$fp" '. + {workspace_fingerprint: $fp}' > "${APP_ROOT}/state/wgpatlas-workspace.json"
