#!/usr/bin/env bash

validate_mirror_snapshot() {
  local manifest="$1"
  local repomd_revision="$2"
  python3 - "$manifest" "$repomd_revision" <<'PY'
import json, sys
from datetime import datetime
from pathlib import Path
manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
repomd_revision = sys.argv[2]
if manifest.get("repo_revision") != repomd_revision:
    print("false")
    raise SystemExit
captured = datetime.fromisoformat(manifest["captured_at"].replace("Z", "+00:00"))
generated = datetime.fromisoformat(manifest["repomd_generated"].replace("Z", "+00:00"))
print("true" if captured >= generated else "false")
PY
}
