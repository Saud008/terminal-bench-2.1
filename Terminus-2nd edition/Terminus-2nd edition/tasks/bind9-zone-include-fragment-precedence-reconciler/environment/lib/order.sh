#!/usr/bin/env bash

# Legacy lexicographic include ordering — not used by compile/export hot path.
# See /app/docs/legacy-ordering.md (deprecated).
lexicographic_include_order() {
  local tree="$1"
  python3 - "$tree" <<'PY'
import json, sys
from pathlib import Path

tree = Path(sys.argv[1])
manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
includes = sorted(manifest.get("includes", []))
print("\n".join(includes))
PY
}

resolve_include_path() {
  local base_file="$1"
  local rel="$2"
  python3 - "$base_file" "$rel" <<'PY'
import sys
from pathlib import Path

base = Path(sys.argv[1]).resolve().parent
rel = sys.argv[2]
print(str((base / rel).resolve()))
PY
}
