#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/golden_proto.sh" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done

[[ -n "${SOL_DIR}" ]] || { echo "golden_proto.sh not found" >&2; exit 1; }

cp -f "${SOL_DIR}/golden_proto.sh" "${APP_ROOT}/lib/netifd/proto.sh"
cp -f "${SOL_DIR}/golden_route_rollback.sh" "${APP_ROOT}/lib/netifd/route_rollback.sh"
cp -f "${SOL_DIR}/golden_hotplug.sh" "${APP_ROOT}/lib/netifd/hotplug.sh"
cp -f "${SOL_DIR}/golden_pd_lease.sh" "${APP_ROOT}/lib/netifd/pd_lease.sh"
cp -f "${SOL_DIR}/golden_state_writer.sh" "${APP_ROOT}/lib/netifd/state_writer.sh"
cp -f "${SOL_DIR}/golden_publish.sh" "${APP_ROOT}/lib/netifd/staging/publish.sh"
cp -f "${SOL_DIR}/golden_export.sh" "${APP_ROOT}/lib/netifd/export.sh"
sed -i 's/\r$//' \
  "${APP_ROOT}/lib/netifd/proto.sh" \
  "${APP_ROOT}/lib/netifd/route_rollback.sh" \
  "${APP_ROOT}/lib/netifd/hotplug.sh" \
  "${APP_ROOT}/lib/netifd/pd_lease.sh" \
  "${APP_ROOT}/lib/netifd/state_writer.sh" \
  "${APP_ROOT}/lib/netifd/staging/publish.sh" \
  "${APP_ROOT}/lib/netifd/export.sh"
chmod +x "${APP_ROOT}/bin/netifd-ctl" \
  "${APP_ROOT}/lib/netifd/"*.sh \
  "${APP_ROOT}/lib/netifd/staging/"*.sh \
  "${APP_ROOT}/scripts/"*.sh
bash "${APP_ROOT}/scripts/reset-state.sh"
