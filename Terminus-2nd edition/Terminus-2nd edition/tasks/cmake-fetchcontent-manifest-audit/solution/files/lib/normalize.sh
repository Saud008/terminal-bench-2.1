#!/usr/bin/env bash
# Path normalization helpers.

normalize_rel() {
  local raw="$1"
  raw="${raw//\\//}"
  while [[ "$raw" == ./* ]]; do raw="${raw#./}"; done
  echo "$raw"
}

join_rel() {
  local base="$1"
  local rel="$2"
  if [[ "$rel" == /* ]]; then
    echo "$(normalize_rel "${rel#/}")"
    return
  fi
  python3 -c 'from pathlib import PurePosixPath
import sys
base, rel = sys.argv[1], sys.argv[2]
parts = []
for p in (PurePosixPath(base) / rel).parts:
    if p in ("", "."):
        continue
    if p == "..":
        if parts:
            parts.pop()
        continue
    parts.append(p)
print("/".join(parts))' "$base" "$rel"
}
