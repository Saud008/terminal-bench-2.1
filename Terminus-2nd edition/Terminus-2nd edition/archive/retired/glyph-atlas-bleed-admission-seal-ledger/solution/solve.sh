#!/usr/bin/env bash
# Self-normalize CRLF before set -e (platform may mount solution with Windows endings).
if grep -q $'\r' "$0" 2>/dev/null; then
  sed -i 's/\r$//' "$0"
  exec bash "$0" "$@"
fi
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export ATLAS_APP_ROOT="${APP_ROOT}"
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

install_golden "${SOL_DIR}/golden_seed.py" "${APP_ROOT}/lib/atlas/seed.py"
install_golden "${SOL_DIR}/golden_catalog.py" "${APP_ROOT}/lib/atlas/catalog.py"
install_golden "${SOL_DIR}/golden_pack.py" "${APP_ROOT}/lib/atlas/pack.py"
install_golden "${SOL_DIR}/golden_compose.py" "${APP_ROOT}/lib/atlas/compose.py"
install_golden "${SOL_DIR}/golden_uv.py" "${APP_ROOT}/lib/atlas/uv.py"
install_golden "${SOL_DIR}/golden_manifest.py" "${APP_ROOT}/lib/atlas/manifest.py"
install_golden "${SOL_DIR}/golden_cli.py" "${APP_ROOT}/lib/atlas/cli.py"

cd "${APP_ROOT}"
make rebuild-atlas
bash "${APP_ROOT}/scripts/reset-state.sh"

# Smoke: sealed export succeeds on catalog scenario
"${APP_ROOT}/bin/atlasd" pack \
  --catalog "${APP_ROOT}/fixtures/catalog.json" \
  --sprites "${APP_ROOT}/fixtures/sprites" \
  --set core-glyphs \
  --seed 7 \
  --atlas-out "${APP_ROOT}/output/oracle-smoke.png" \
  --manifest-out "${APP_ROOT}/output/oracle-smoke.json"
