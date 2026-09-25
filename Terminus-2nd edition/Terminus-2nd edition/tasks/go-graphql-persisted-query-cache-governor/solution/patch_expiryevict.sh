#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/expiryevict/policy.go")
text = path.read_text(encoding="utf-8")
old = "\tage := nowMs - op.RegisteredAtMs"
new = "\tage := nowMs - op.LastSeenMs"
if old not in text:
    raise SystemExit("expiryevict anchor missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
