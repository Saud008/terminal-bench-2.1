#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/bin:${PATH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_cycle.sh" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_cycle.sh not found" >&2; exit 1; }

cp -f "${SOL}/golden_cycle.sh" "${APP_ROOT}/lib/cycle.sh"
cp -f "${SOL}/golden_topo.sh" "${APP_ROOT}/lib/topo.sh"
cp -f "${SOL}/golden_merge.sh" "${APP_ROOT}/lib/merge.sh"
cp -f "${SOL}/golden_rpath.sh" "${APP_ROOT}/lib/rpath.sh"
cp -f "${SOL}/golden_graph.sh" "${APP_ROOT}/lib/graph.sh"
cp -f "${SOL}/golden_stage.sh" "${APP_ROOT}/lib/stage.sh"
cp -f "${SOL}/golden_publish.sh" "${APP_ROOT}/lib/publish.sh"
cp -f "${SOL}/golden_linkorder.sh" "${APP_ROOT}/lib/linkorder.sh"
cp -f "${SOL}/golden_validate.sh" "${APP_ROOT}/lib/validate.sh"

for libfile in graph cycle topo merge rpath stage publish linkorder validate ingest; do
  sed -i 's/\r$//' "${APP_ROOT}/lib/${libfile}.sh"
done

make -C "${APP_ROOT}/libltparse" ltparse
install -m 755 "${APP_ROOT}/libltparse/ltparse" /usr/local/bin/ltparse
bash "${APP_ROOT}/scripts/rebuild-demo-libs.sh"
bash "${APP_ROOT}/scripts/reset-state.sh"
/app/bin/lt-canonicalize /app/projects/demo --out /app/output/libtool-manifest.json
