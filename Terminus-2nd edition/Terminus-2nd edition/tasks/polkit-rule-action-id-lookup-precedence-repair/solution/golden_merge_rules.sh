#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pk_merge_rules() {
  local stack="$1"
  local dir
  dir="$(rules_dir_for "$stack")"
  python3 - "$dir" <<'PY'
import json, re, sys
from pathlib import Path

root = Path(sys.argv[1])

def prefix(name):
    m = re.match(r"^(\d+)-", name)
    return (int(m.group(1)), name) if m else (999999, name)

files = sorted(root.glob("*.rules"), key=lambda p: prefix(p.name))
blocks = []

def parse_file(path):
    cur = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "block":
            cur = {}
        elif line == "end":
            if cur:
                blocks.append({**cur, "source_file": path.name})
            cur = {}
        elif "=" in line:
            k, v = line.split("=", 1)
            cur[k.strip()] = v.strip()

for path in files:
    parse_file(path)
print(json.dumps(blocks))
PY
}
