#!/usr/bin/env bash
# Flatten stack JSON with include expansion.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

PAMREPLAY_MAX_INCLUDE_DEPTH=8

pamreplay_flatten_stack() {
  local stack_file="$1"
  pamreplay_validate_paths || return 1
  python3 - "$stack_file" "$PAMREPLAY_STACKS_ROOT" "$PAMREPLAY_MAX_INCLUDE_DEPTH" <<'PY'
import json, sys
from pathlib import Path

stack_file = Path(sys.argv[1])
stacks_root = Path(sys.argv[2])
max_depth = int(sys.argv[3])

def load_entries(path: Path, depth: int) -> list:
    if depth >= max_depth:
        raise ValueError("include depth exceeded")
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for entry in data.get("entries", []):
        if "include" in entry:
            rel = entry["include"]
            inc_path = stacks_root / rel
            if not inc_path.is_file():
                raise FileNotFoundError(rel)
            out.extend(load_entries(inc_path, depth + 1))
        else:
            out.append(entry)
    return out

try:
    flat = load_entries(stack_file, 1)
    meta = json.loads(stack_file.read_text(encoding="utf-8"))
    print(json.dumps({"stack_id": meta.get("stack_id", ""), "service": meta.get("service", ""), "entries": flat}))
except Exception as exc:
    print(json.dumps({"error": str(exc)}))
    sys.exit(2)
PY
}
