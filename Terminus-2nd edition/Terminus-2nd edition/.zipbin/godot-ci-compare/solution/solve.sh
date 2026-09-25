#!/usr/bin/env bash
# Self-normalize CRLF before set -e (platform may mount solution with Windows endings).
if grep -q $'\r' "$0" 2>/dev/null; then
  sed -i 's/\r$//' "$0"
  exec bash "$0" "$@"
fi
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export TSCN_APP_ROOT="${APP_ROOT}"
export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for root in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  for candidate in "${root}/files" "${root}"; do
    if [[ -f "${candidate}/golden_remap.sh" ]]; then
      SOL_DIR="${candidate}"
      break 2
    fi
  done
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_remap.sh not found" >&2; exit 1; }

for golden in remap merge graph ledger orphan; do
  src="${SOL_DIR}/golden_${golden}.sh"
  dst="${APP_ROOT}/lib/tscn/${golden}.sh"
  sed 's/\r$//' "${src}" > "${dst}"
done

cd "${APP_ROOT}"
make rebuild-tscn
bash "${APP_ROOT}/scripts/reset-state.sh"

# Smoke check: golden libs load and sealed export succeeds on catalog scenario
"${APP_ROOT}/bin/tscn-merge" apply \
  --tree "${APP_ROOT}/fixtures/trees/village-remap" \
  --base base \
  --left left \
  --right right \
  --seed 4 \
  --export "${APP_ROOT}/output/oracle-smoke.json"
