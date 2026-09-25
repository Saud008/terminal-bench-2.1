#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/temporalceiling/ceiling_delta.go")
text = path.read_text(encoding="utf-8")
old = """func EligibleDelta(amendments []Amendment, grantID, expenseDate string) int64 {
\t_ = expenseDate
\tvar out int64
\tfor _, a := range amendments {
\t\tif a.GrantID == grantID {
\t\t\tout += a.DeltaCents
\t\t}
\t}
\treturn out
}"""
new = """func EligibleDelta(amendments []Amendment, grantID, expenseDate string) int64 {
\tvar out int64
\tfor _, a := range amendments {
\t\tif a.GrantID != grantID {
\t\t\tcontinue
\t\t}
\t\tif expenseDate == \"\" {
\t\t\tcontinue
\t\t}
\t\tif a.EffectiveDate > expenseDate {
\t\t\tcontinue
\t\t}
\t\tout += a.DeltaCents
\t}
\treturn out
}"""
if old not in text:
    raise SystemExit("temporalceiling anchor missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
