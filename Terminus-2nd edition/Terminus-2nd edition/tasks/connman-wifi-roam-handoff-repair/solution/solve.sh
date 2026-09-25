#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [[ -f "${candidate}/golden_fsm.sh" ]]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_fsm.sh not found" >&2; exit 1; }

cp -f "${SOL}/golden_fsm.sh" "${APP_ROOT}/lib/roam/fsm.sh"
cp -f "${SOL}/golden_scan_ledger.sh" "${APP_ROOT}/lib/roam/scan_ledger.sh"
cp -f "${SOL}/golden_service_rank.sh" "${APP_ROOT}/lib/roam/service_rank.sh"
cp -f "${SOL}/golden_consent.sh" "${APP_ROOT}/lib/roam/consent.sh"
cp -f "${SOL}/golden_dhcp_hook.sh" "${APP_ROOT}/lib/roam/dhcp_hook.sh"

for f in \
  "${APP_ROOT}/lib/roam/fsm.sh" \
  "${APP_ROOT}/lib/roam/scan_ledger.sh" \
  "${APP_ROOT}/lib/roam/service_rank.sh" \
  "${APP_ROOT}/lib/roam/consent.sh" \
  "${APP_ROOT}/lib/roam/dhcp_hook.sh"; do
  sed -i 's/\r$//' "$f"
done

chmod +x "${APP_ROOT}/scripts/connman-roamctl" "${APP_ROOT}/lib/roam/"*.sh "${APP_ROOT}/scripts/"*.sh
bash "${APP_ROOT}/scripts/reset-state.sh"
