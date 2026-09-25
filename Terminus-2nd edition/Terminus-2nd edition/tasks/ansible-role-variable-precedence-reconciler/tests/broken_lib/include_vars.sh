#!/usr/bin/env bash

resolve_include_vars() {
  local playbook_dir="$1"
  local manifest="$2"
  python3 - "$playbook_dir" "$manifest" <<'PY'
import json, subprocess, sys
from pathlib import Path

playbook_dir = Path(sys.argv[1])
manifest = json.loads(sys.argv[2])
includes = manifest.get("include_vars", [])
paths = []
for entry in includes:
    rel = entry["path"]
    paths.append(str((playbook_dir / rel).resolve()))
paths.sort()
merged = {}
loader = "/app/tools/var_loader.py"
for path in paths:
    proc = subprocess.run(
        [sys.executable, loader, "touch-load", "--file", path],
        capture_output=True, text=True, check=True,
    )
    chunk = json.loads(proc.stdout)
    merged.update(chunk)
print(json.dumps(merged, sort_keys=True))
PY
}
