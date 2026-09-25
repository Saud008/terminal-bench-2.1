#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution"; do
  if [[ -f "${candidate}/golden_kv_ingest.sh" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_kv_ingest.sh not found" >&2; exit 1; }

for mod in kv_ingest kv_replay kv_weight kv_priority kv_advert kv_race kv_staging kv_notify kv_export; do
  sed 's/\r$//' "${SOL_DIR}/golden_${mod}.sh" > "/app/lib/${mod}.sh"
done
chmod +x /app/lib/kv_*.sh
bash /app/scripts/reset-state.sh
