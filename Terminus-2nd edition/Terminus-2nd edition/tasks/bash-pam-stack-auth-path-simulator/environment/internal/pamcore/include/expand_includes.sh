#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../parse/pam_parse.sh"

expand_service_file() {
  local service_path="$1"
  local base_dir
  base_dir="$(dirname "$service_path")"
  python3 - "$service_path" "$base_dir" <<'PY'
import json, sys
from pathlib import Path

service_path = Path(sys.argv[1])
base_dir = Path(sys.argv[2])

def parse_lines(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            rows.append({"kind": "directive", "text": line})
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        rows.append({
            "kind": "module",
            "type": parts[0],
            "control": parts[1],
            "module": parts[2],
            "args": parts[3:],
        })
    return rows

def expand(path, base):
    out = []
    stack_depth = 0
    for row in parse_lines(path):
        if row["kind"] == "directive":
            text = row["text"]
            if text.startswith("@include "):
                inc = text.split(None, 1)[1].strip()
                # include anchor uses scenario root
                inc_path = base_dir.parent / inc
                out.extend(expand(inc_path, base))
            elif text.startswith("@include-substack "):
                inc = text.split(None, 1)[1].strip()
                inc_path = base / inc
                stack_depth += 1
                out.extend(expand(inc_path, inc_path.parent))
                # substack frame retained for nested expansion
                if stack_depth > 0:
                    out.extend(expand(inc_path, inc_path.parent))
            continue
        out.append(row)
    return out

base_dir = Path(sys.argv[2])
expanded = expand(service_path, service_path.parent)
print(json.dumps(expanded))
PY
}
