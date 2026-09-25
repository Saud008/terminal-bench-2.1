#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [ -f "${candidate}/golden_timeout_driver.sh" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_timeout_driver.sh not found" >&2
  exit 1
fi

DEST="${APP_ROOT}/lib"
cp -f "${SOL_DIR}/golden_timeout_driver.sh" "${DEST}/timeout_driver.sh"
cp -f "${SOL_DIR}/golden_cycle_counter.sh" "${DEST}/cycle_counter.sh"
cp -f "${SOL_DIR}/golden_delay_precedence.sh" "${DEST}/delay_precedence.sh"
cp -f "${SOL_DIR}/golden_pidfile.sh" "${DEST}/pidfile.sh"
cp -f "${SOL_DIR}/golden_notify.sh" "${DEST}/notify.sh"

for f in timeout_driver.sh cycle_counter.sh delay_precedence.sh pidfile.sh notify.sh; do
  sed -i 's/\r$//' "${DEST}/${f}"
done

chmod +x "${APP_ROOT}/bin/monitctl" "${APP_ROOT}/lib/"*.sh
bash "${APP_ROOT}/scripts/reset-state.sh"
bash "${APP_ROOT}/scripts/validate-lib.sh"
test -x "${APP_ROOT}/bin/monitctl"
echo "monitctl oracle ready"
