#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_stack.sh" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_stack.sh not found" >&2
  exit 1
fi

DEST="${APP_ROOT}/lib"
cp -f "${SOL_DIR}/golden_stack.sh" "${DEST}/stack.sh"
cp -f "${SOL_DIR}/golden_runner.sh" "${DEST}/runner.sh"
cp -f "${SOL_DIR}/golden_environment.sh" "${DEST}/environment.sh"
cp -f "${SOL_DIR}/golden_audit.sh" "${DEST}/audit.sh"
cp -f "${SOL_DIR}/golden_compose.sh" "${DEST}/compose.sh"
cp -f "${SOL_DIR}/golden_staging.sh" "${DEST}/staging.sh"
cp -f "${SOL_DIR}/golden_outcome.sh" "${DEST}/outcome.sh"
cp -f "${SOL_DIR}/golden_outcome_guard.sh" "${DEST}/outcome_guard.sh"
cp -f "${SOL_DIR}/golden_export.sh" "${DEST}/export.sh"

for f in "${DEST}/stack.sh" "${DEST}/runner.sh" "${DEST}/environment.sh" "${DEST}/audit.sh" "${DEST}/compose.sh" "${DEST}/staging.sh" "${DEST}/outcome.sh" "${DEST}/outcome_guard.sh" "${DEST}/export.sh"; do
  sed -i 's/\r$//' "$f"
done

chmod +x "${APP_ROOT}/bin/pamreplay" "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/scripts/"*.sh
bash "${APP_ROOT}/scripts/reset-state.sh"
