#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
STATE_DIR="${APP_ROOT}/state"
source "${APP_ROOT}/lib/common.sh"

pair_id=""
output=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pair) pair_id="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[ -n "${pair_id}" ] && [ -n "${output}" ] || exit 2
[ -f "${STATE_DIR}/staging-meta.json" ] || exit 3

active=$(cat "${STATE_DIR}/active-pair.id" 2>/dev/null || true)
[ "${active}" = "${pair_id}" ] || exit 3

# export path reopens iptables/nft sources instead of staging-only
manifest="/app/fixtures/pairs/${pair_id}/pair.json"
ipt_path=$(python3 -c "import json; print(json.load(open('${manifest}'))['iptables_path'])")
nft_path=$(python3 -c "import json; print(json.load(open('${manifest}'))['nft_path'])")

bash "${APP_ROOT}/lib/export_report.sh" \
  "${STATE_DIR}" "${pair_id}" "${output}" "${manifest}" "${ipt_path}" "${nft_path}"
exit 0
