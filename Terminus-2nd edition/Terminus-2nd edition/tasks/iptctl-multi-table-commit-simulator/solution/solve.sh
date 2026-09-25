#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
LIB="${APP_ROOT}/lib"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/files" && pwd)"
ORACLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/oracle" && pwd)"
export PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

mkdir -p "${LIB}"

install -m 0755 "${PATCH_DIR}/patch_rule_lexer.sh" "${LIB}/rule_lexer.sh"
install -m 0755 "${PATCH_DIR}/patch_table_commit_order.sh" "${LIB}/table_commit_order.sh"
install -m 0755 "${PATCH_DIR}/patch_chain_policy_mode.sh" "${LIB}/chain_policy_mode.sh"
install -m 0755 "${PATCH_DIR}/patch_rule_counter_mode.sh" "${LIB}/rule_counter_mode.sh"
install -m 0755 "${PATCH_DIR}/patch_nat_mark_bridge.sh" "${LIB}/nat_mark_bridge.sh"
install -m 0755 "${PATCH_DIR}/patch_ct_order_mode.sh" "${LIB}/ct_order_mode.sh"
install -m 0755 "${PATCH_DIR}/patch_plan_binding.sh" "${LIB}/plan_binding.sh"
install -m 0755 "${PATCH_DIR}/patch_merge_stage_writer.sh" "${LIB}/merge_stage_writer.sh"
install -m 0755 "${ORACLE_DIR}/patch_export_gate.sh" "${LIB}/export_gate.sh"
install -m 0755 "${ORACLE_DIR}/patch_report_emit.sh" "${LIB}/report_emit.sh"

python3 - <<'PY'
import json
import subprocess
from pathlib import Path

app = Path("/app")
restore = app / "fixtures/restores/core-filter.v4"
out = app / "output/oracle-smoke.json"
subprocess.run(
    [str(app / "scripts/iptctl"), "simulate", "--restore", str(restore), "--seed", "1", "--export", str(out)],
    check=True,
)
report = json.loads(out.read_text(encoding="utf-8"))
assert report.get("exit_code") == 0, report
assert report.get("commit_order"), report
PY

bash "${APP_ROOT}/scripts/reset-state.sh"
test -x "${APP_ROOT}/scripts/iptctl"
test -x /usr/local/bin/iptctl
echo "iptctl oracle ready"
