#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/tenantquota/account.go")
text = path.read_text(encoding="utf-8")
old = "func CountTowardQuota(ops []model.LedgerOperation) int {\n\treturn len(ops)\n}"
new = """func CountTowardQuota(ops []model.LedgerOperation) int {
\tn := 0
\tfor _, op := range ops {
\t\tif op.Status == "active" {
\t\t\tn++
\t\t}
\t}
\treturn n
}"""
if old not in text:
    raise SystemExit("tenantquota anchor missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
