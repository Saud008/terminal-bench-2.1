#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/categoryguard/category_ok.go")
text = path.read_text(encoding="utf-8")
old = """func AllowedCategory(category string, allowed []string) bool {
\t_ = category
\t_ = allowed
\treturn true
}"""
new = """func AllowedCategory(category string, allowed []string) bool {
\tfor _, item := range allowed {
\t\tif item == category {
\t\t\treturn true
\t\t}
\t}
\treturn false
}"""
if old not in text:
    raise SystemExit("categoryguard anchor missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
