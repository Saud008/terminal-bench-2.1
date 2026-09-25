#!/usr/bin/env bash
# Prefix path canonicalization.

prefix_canonicalize() {
  local prefix_root="$1"
  local relative_path="$2"
  PREFIX_CANONICAL=""

  if [[ -z "$relative_path" ]]; then
    return 0
  fi

  local joined="${prefix_root%/}/${relative_path}"
  PREFIX_CANONICAL="$(cd "$(dirname "${joined}")" 2>/dev/null && pwd)/$(basename "${joined}")"
}
