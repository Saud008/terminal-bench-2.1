#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORACLE_DIR=""
for candidate in "${SCRIPT_DIR}/oracle" "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/semantic_engine.py" ]; then
    ORACLE_DIR="${candidate}"
    break
  fi
done

if [ -z "${ORACLE_DIR}" ]; then
  echo "oracle: semantic_engine.py not found" >&2
  exit 1
fi

install_file() {
  local src_name="$1"
  local dest_path="$2"
  local mode="$3"
  install -m "${mode}" "${ORACLE_DIR}/${src_name}" "${dest_path}"
  sed -i 's/\r$//' "${dest_path}" 2>/dev/null || true
}

install_file semantic_engine.py "${APP_ROOT}/lib/risk_engine.py" 0644
install_file patch_ingest.sh "${APP_ROOT}/lib/ingest.sh" 0755
install_file patch_export.sh "${APP_ROOT}/lib/export.sh" 0755

if [ -f "${ORACLE_DIR}/patch_parse_ipt.awk" ]; then
  install_file patch_parse_ipt.awk "${APP_ROOT}/lib/parse_ipt.awk" 0644
fi
if [ -f "${ORACLE_DIR}/patch_normalize_match.awk" ]; then
  install_file patch_normalize_match.awk "${APP_ROOT}/lib/normalize_match.awk" 0644
fi

chmod +x "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/scripts/fw-risk-map"
sed -i 's/\r$//' "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/scripts/fw-risk-map" 2>/dev/null || true

python3 -c "import importlib.util; spec=importlib.util.spec_from_file_location('risk_engine', '${APP_ROOT}/lib/risk_engine.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); assert hasattr(mod, 'ingest_pair')"

bash "${APP_ROOT}/scripts/reset-state.sh"
test -x "${APP_ROOT}/scripts/fw-risk-map"
test -x /usr/local/bin/fw-risk-map
echo "fw-risk-map oracle ready"
