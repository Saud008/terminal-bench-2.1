#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/manifestload/parse.go")
text = path.read_text(encoding="utf-8")
old = "\tsum := sha256.Sum256([]byte(query))"
new = "\tnorm := NormalizeQuery(query)\n\tsum := sha256.Sum256([]byte(norm))"
if old not in text:
    raise SystemExit("manifestload anchor missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
if "NormalizeQuery(query)" not in path.read_text(encoding="utf-8"):
    raise SystemExit("manifestload post-check failed")
PY
test -f /app/internal/manifestload/parse.go
