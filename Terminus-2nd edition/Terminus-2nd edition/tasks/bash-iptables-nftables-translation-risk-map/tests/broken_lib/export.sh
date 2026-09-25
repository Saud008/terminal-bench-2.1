#!/usr/bin/env bash
set -euo pipefail
# Partial trap: export re-reads sources (staging-only violation)
APP_ROOT="${APP_ROOT:-/app}"
STATE_DIR="${APP_ROOT}/state"
source "${APP_ROOT}/lib/common.sh"
pair_id=""
output=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pair) pair_id="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) shift ;;
  esac
done
manifest="/app/fixtures/pairs/${pair_id}/pair.json"
bash "${APP_ROOT}/lib/ingest.sh" --pair "${manifest}"
bash "${APP_ROOT}/lib/export_report.sh" "${STATE_DIR}" "${pair_id}" "${output}" "${manifest}" \
  "$(python3 -c "import json; print(json.load(open('${manifest}'))['iptables_path'])")" \
  "$(python3 -c "import json; print(json.load(open('${manifest}'))['nft_path'])")"
