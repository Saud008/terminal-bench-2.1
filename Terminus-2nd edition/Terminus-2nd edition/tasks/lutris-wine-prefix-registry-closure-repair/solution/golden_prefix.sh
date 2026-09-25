#!/usr/bin/env bash
# Prefix path canonicalization with full symlink resolution.

prefix_canonicalize() {
  local prefix_root="$1"
  local relative_path="$2"
  PREFIX_CANONICAL=""

  if [[ -z "$relative_path" ]]; then
    return 0
  fi

  local joined="${prefix_root%/}/${relative_path}"
  PREFIX_CANONICAL="$(python3 - "$joined" <<'PY'
import os
import sys

path = sys.argv[1]
print(os.path.realpath(path))
PY
)"
}
