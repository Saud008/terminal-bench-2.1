#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="${APP_ROOT:-/app}"

cp -f "${SCRIPT_DIR}/golden_conf_parse.sh" "${APP_ROOT}/lib/conf_parse.sh"
cp -f "${SCRIPT_DIR}/golden_section_order.sh" "${APP_ROOT}/lib/section_order.sh"
cp -f "${SCRIPT_DIR}/golden_remount.sh" "${APP_ROOT}/lib/remount.sh"
cp -f "${SCRIPT_DIR}/golden_validate.sh" "${APP_ROOT}/lib/validate.sh"
sed -i 's/\r$//' "${APP_ROOT}/lib/"*.sh
chmod +x "${APP_ROOT}/bin/dosbox-plan" "${APP_ROOT}/lib/"*.sh
bash "${APP_ROOT}/scripts/reset-state.sh"
