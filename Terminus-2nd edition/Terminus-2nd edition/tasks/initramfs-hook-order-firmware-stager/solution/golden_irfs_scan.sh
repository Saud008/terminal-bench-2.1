#!/usr/bin/env bash
# Rootfs digest — oracle tree walk per staging-ledger.md

irfs_rootfs_digest() {
  local root="$1"
  python3 - "$root" <<'PY'
import hashlib, sys
from pathlib import Path
root = Path(sys.argv[1])
h = hashlib.sha256()
for f in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
    rel = f.relative_to(root).as_posix()
    h.update(rel.encode("utf-8"))
    h.update(f.read_bytes())
print(h.hexdigest())
PY
}

irfs_file_digest() {
  local file="$1"
  sha256sum "$file" | awk '{print $1}'
}

irfs_file_size() {
  local file="$1"
  wc -c < "$file" | tr -d ' '
}
