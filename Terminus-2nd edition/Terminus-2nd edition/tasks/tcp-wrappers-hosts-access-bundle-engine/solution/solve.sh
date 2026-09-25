#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}/files" \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_merge.sh" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_merge.sh not found" >&2
  exit 1
fi

DEST="${APP_ROOT}/lib"
cp -f "${SOL_DIR}/golden_common.sh" "${DEST}/common.sh"
cp -f "${SOL_DIR}/golden_parse.sh" "${DEST}/parse.sh"
cp -f "${SOL_DIR}/golden_merge.sh" "${DEST}/merge.sh"
cp -f "${SOL_DIR}/golden_cidr.sh" "${DEST}/cidr.sh"
cp -f "${SOL_DIR}/golden_decide.sh" "${DEST}/decide.sh"
cp -f "${SOL_DIR}/golden_aliases.sh" "${DEST}/aliases.sh"
cp -f "${SOL_DIR}/golden_replay.sh" "${DEST}/replay.sh"
cp -f "${SOL_DIR}/golden_publish.sh" "${DEST}/publish.sh"
sed -i 's/\r$//' "${DEST}"/*.sh "${APP_ROOT}/bin/hostsctl"

chmod +x "${APP_ROOT}/bin/hostsctl" "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/scripts/"/*.sh
bash "${APP_ROOT}/scripts/reset-state.sh"
