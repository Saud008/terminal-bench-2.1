#!/usr/bin/env bash

validate_mirror_snapshot() {
  local manifest="$1"
  local repomd_revision="$2"
  python3 - "$manifest" "$repomd_revision" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
captured = datetime.fromisoformat(manifest["captured_at"].replace("Z", "+00:00"))
now = datetime.now(timezone.utc)
age = (now - captured).total_seconds()
print("true" if age < 86400 * 30 else "false")
PY
}
