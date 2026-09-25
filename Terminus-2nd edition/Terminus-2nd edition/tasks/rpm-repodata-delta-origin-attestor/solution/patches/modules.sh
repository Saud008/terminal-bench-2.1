#!/usr/bin/env bash

parse_module_defaults() {
  local modules_yaml="$1"
  python3 - "$modules_yaml" <<'PY'
import json, sys
from pathlib import Path
import yaml
data = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
defaults = data.get("data", {}).get("module_defaults", [])
rows = []
for entry in defaults:
    rows.append({
        "module": entry.get("module_name", ""),
        "default_stream": entry.get("stream_name", ""),
        "default_profile": entry.get("default_profile", ""),
    })
print(json.dumps(rows))
PY
}
