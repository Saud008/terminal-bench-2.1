#!/usr/bin/env bash
# Compression tags — broken baseline uses case-sensitive suffix lookup.

irfs_compress_tag() {
  local path="$1"
  local config_path="$2"
  PATH_ARG="${path}" CONFIG="${config_path}" python3 <<'PY'
import json, os, sys
from pathlib import Path
path = os.environ["PATH_ARG"]
cfg = json.load(open(os.environ["CONFIG"], encoding="utf-8"))
comp = cfg.get("compression", {})
default = comp.get("default", "none")
# baseline: case-sensitive suffix only
suffix = Path(path).suffix
print(comp.get(suffix, default))
PY
}
