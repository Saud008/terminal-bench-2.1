#!/usr/bin/env bash
# Self-normalize CRLF before set -e (platform may mount solution with Windows endings).
if grep -q $'\r' "$0" 2>/dev/null; then
  sed -i 's/\r$//' "$0"
  exec bash "$0" "$@"
fi
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export SHEET_APP_ROOT="${APP_ROOT}"
export PYTHONPATH="${APP_ROOT}/lib:${PYTHONPATH:-}"
export PATH="${APP_ROOT}/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for root in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  for candidate in "${root}/files" "${root}"; do
    if [[ -f "${candidate}/golden_catalog.py" ]]; then
      SOL_DIR="${candidate}"
      break 2
    fi
  done
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_catalog.py not found" >&2; exit 1; }

install_golden() {
  local src="$1"
  local dst="$2"
  sed 's/\r$//' "${src}" > "${dst}"
}

install_golden "${SOL_DIR}/golden_seed.py" "${APP_ROOT}/lib/sheet/seed.py"
install_golden "${SOL_DIR}/golden_catalog.py" "${APP_ROOT}/lib/sheet/catalog.py"
install_golden "${SOL_DIR}/golden_impose.py" "${APP_ROOT}/lib/sheet/impose.py"
install_golden "${SOL_DIR}/golden_compose.py" "${APP_ROOT}/lib/sheet/compose.py"
install_golden "${SOL_DIR}/golden_window.py" "${APP_ROOT}/lib/sheet/window.py"
install_golden "${SOL_DIR}/golden_ledger.py" "${APP_ROOT}/lib/sheet/ledger.py"
install_golden "${SOL_DIR}/golden_cli.py" "${APP_ROOT}/lib/sheet/cli.py"

cd "${APP_ROOT}"
make rebuild-sheet
bash "${APP_ROOT}/scripts/reset-state.sh"

# Smoke: sealed export succeeds on catalog scenario
"${APP_ROOT}/bin/sheetd" impose \
  --catalog "${APP_ROOT}/fixtures/catalog.json" \
  --marks "${APP_ROOT}/fixtures/marks" \
  --set core-marks \
  --seed 7 \
  --sheet-out "${APP_ROOT}/output/oracle-smoke.png" \
  --ledger-out "${APP_ROOT}/output/oracle-smoke.json"
