#!/usr/bin/env bash

# Staging-side digest helper — see /app/docs/legacy-bindings.md (deprecated).
legacy_staging_digest() {
  local snap="$1"
  python3 - "$snap" <<'PY'
import hashlib, json, sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
digest = hashlib.sha256(
    json.dumps(meta["effective"], sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
print(digest)
PY
}
