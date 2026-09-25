#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/policyoverlap/overlap_pick.go")
text = path.read_text(encoding="utf-8")
text = text.replace("len(c.RestrictionPath) < len(best.RestrictionPath)", "len(c.RestrictionPath) > len(best.RestrictionPath)", 1)
path.write_text(text, encoding="utf-8")
PY
