#!/usr/bin/env bash
# Rootfs digest — baseline uses directory basename only.

irfs_rootfs_digest() {
  local root="$1"
  python3 - "$root" <<'PY'
import hashlib, sys
from pathlib import Path
root = Path(sys.argv[1])
# Baseline: basename only, not full tree walk
print(hashlib.sha256(root.name.encode()).hexdigest())
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
