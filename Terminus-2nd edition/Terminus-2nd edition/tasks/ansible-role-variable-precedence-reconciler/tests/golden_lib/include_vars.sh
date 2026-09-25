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
behaviour = manifest.get("hash_behaviour", "replace")
includes = sorted(includes, key=lambda item: int(item["depth"]))

def deep_merge(base, overlay):
    out = dict(base)
    for key, value in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out

merged = {}
loader = "/app/tools/var_loader.py"
for entry in includes:
    path = str((playbook_dir / entry["path"]).resolve())
    proc = subprocess.run(
        [sys.executable, loader, "touch-load", "--file", path],
        capture_output=True, text=True, check=True,
    )
    chunk = json.loads(proc.stdout)
    if behaviour == "merge":
        merged = deep_merge(merged, chunk)
    else:
        merged.update(chunk)
print(json.dumps(merged, sort_keys=True))
PY
}
