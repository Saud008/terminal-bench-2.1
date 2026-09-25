#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/golden_parse_porcelain.sh" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [[ -z "${SOL_DIR}" ]]; then
  echo "oracle: golden_parse_porcelain.sh not found" >&2
  exit 1
fi

cp -f "${SOL_DIR}/golden_parse_porcelain.sh" "${APP_ROOT}/lib/parse_porcelain.sh"
cp -f "${SOL_DIR}/golden_classify.sh" "${APP_ROOT}/lib/classify.sh"
sed -i 's/\r$//' "${APP_ROOT}/lib/parse_porcelain.sh" "${APP_ROOT}/lib/classify.sh"
chmod +x "${APP_ROOT}/bin/wtstatus-export" "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/scripts/"*.sh
bash "${APP_ROOT}/scripts/reset-state.sh"
