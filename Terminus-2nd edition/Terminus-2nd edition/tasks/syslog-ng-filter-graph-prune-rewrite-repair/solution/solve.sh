#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/golden_replay.sh" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done

[[ -n "${SOL_DIR}" ]] || { echo "golden_replay.sh not found" >&2; exit 1; }

cp -f "${SOL_DIR}/golden_boolean.sh" "${APP_ROOT}/lib/boolean.sh"
cp -f "${SOL_DIR}/golden_prune.sh" "${APP_ROOT}/lib/prune.sh"
cp -f "${SOL_DIR}/golden_branch.sh" "${APP_ROOT}/lib/branch.sh"
cp -f "${SOL_DIR}/golden_cache.sh" "${APP_ROOT}/lib/cache.sh"
cp -f "${SOL_DIR}/golden_replay.sh" "${APP_ROOT}/lib/replay.sh"

chmod +x "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/bin/syslogctl" "${APP_ROOT}/scripts/"*.sh
bash "${APP_ROOT}/scripts/reset-state.sh"
