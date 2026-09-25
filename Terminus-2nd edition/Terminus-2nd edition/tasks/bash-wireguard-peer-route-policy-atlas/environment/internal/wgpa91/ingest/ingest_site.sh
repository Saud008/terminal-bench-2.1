#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/wgpa91/parse/parse_wg_conf.sh"

site=""
run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --site) site="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
done
[[ -n "$site" && -n "$run_id" ]] || exit 2

root="${TB3_SITE_ROOT:-${APP_ROOT}/sites}"
base="${root}/${site}"
manifest=$(cat "${base}/manifest.json")
policy=$(cat "${base}/site-policy.json")
configs="[]"
routes="[]"
while IFS= read -r iface; do
  [[ -z "$iface" ]] && continue
  conf="${base}/wg/${iface}.conf"
  parsed=$(parse_wg_conf "$conf")
  configs=$(echo "$configs" | jq --argjson p "$parsed" --arg i "$iface" '. + [($p + {interface: $i})]')
  rfile="${base}/routes/${iface}-routes.json"
  if [[ -f "$rfile" ]]; then
    routes=$(echo "$routes" | jq --argjson r "$(cat "$rfile")" '. + [$r]')
  fi
done < <(echo "$manifest" | jq -r '.interfaces[]')

mkdir -p "${APP_ROOT}/work"
jq -n --arg site "$site" --argjson manifest "$manifest" --argjson policy "$policy" \
  --argjson configs "$configs" --argjson routes "$routes" \
  '{site: $site, manifest: $manifest, policy: $policy, configs: $configs, routes: $routes}' \
  > "${APP_ROOT}/work/${run_id}-ingest.json"
echo "ingested ${site} for ${run_id}"
