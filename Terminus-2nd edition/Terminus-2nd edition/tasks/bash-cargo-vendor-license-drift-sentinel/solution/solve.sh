#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORACLE_DIR=""
for candidate in "${SCRIPT_DIR}/oracle" "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/vendor_audit_engine.py" ]; then
    ORACLE_DIR="${candidate}"
    break
  fi
done

if [ -z "${ORACLE_DIR}" ]; then
  echo "oracle: vendor_audit_engine.py not found" >&2
  exit 1
fi

install_file() {
  local src_name="$1"
  local dest_path="$2"
  local mode="$3"
  if [ ! -f "${ORACLE_DIR}/${src_name}" ]; then
    echo "oracle: missing ${src_name}" >&2
    exit 1
  fi
  install -m "${mode}" "${ORACLE_DIR}/${src_name}" "${dest_path}"
  sed -i 's/\r$//' "${dest_path}" 2>/dev/null || true
}

install_file vendor_audit_engine.py "${APP_ROOT}/audit/compliance_engine.py" 0644
install_file fix_publish_manifest.sh "${APP_ROOT}/lib/publish_manifest.sh" 0755

chmod +x "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/scripts/cvls-governor"
sed -i 's/\r$//' "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/scripts/cvls-governor" 2>/dev/null || true

python3 <<'PY'
import importlib.util
import sys
from pathlib import Path

app = Path("/app")
engine = app / "audit/compliance_engine.py"
spec = importlib.util.spec_from_file_location("compliance_engine", engine)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
for name in (
    "ingest_workspace",
    "audit_staging",
    "export_report",
    "workspace_fingerprint",
    "parse_cargo_lock",
):
    assert hasattr(mod, name), f"missing {name}"
print("compliance_engine contract ok")
PY

bash "${APP_ROOT}/scripts/reset-state.sh"
bash "${APP_ROOT}/scripts/rebuild-sentinel.sh"

WS="${APP_ROOT}/fixtures/workspaces/baseline"
OUT_JSON="${APP_ROOT}/output/oracle-smoke.json"
OUT_CSV="${APP_ROOT}/output/oracle-smoke.csv"
mkdir -p "${APP_ROOT}/output"

cvls-governor inventory --workspace "${WS}"
cvls-governor attest --workspace "${WS}"
cvls-governor publish --workspace "${WS}" --json "${OUT_JSON}" --csv "${OUT_CSV}"

python3 <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/app/output/oracle-smoke.json").read_text(encoding="utf-8"))
assert report.get("schema_version") == "1"
assert "findings" in report and "summary" in report
assert Path("/app/output/oracle-smoke.csv").is_file()
print("publish smoke ok")
PY

test -x "${APP_ROOT}/scripts/cvls-governor"
test -x /usr/local/bin/cvls-governo
echo "cvls-governor oracle ready"
