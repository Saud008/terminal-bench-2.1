#!/usr/bin/env bash
# Parse .gitattributes and resolve filter=gcrypt paths.

# shellcheck source=gc_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/gc_common.sh"

GC_ATTR_CACHE_FILE=""

gc_attrs_load() {
  local repo="$1"
  GC_ATTR_CACHE_FILE="${repo}/.gitattributes"
  [[ -f "$GC_ATTR_CACHE_FILE" ]]
}

gc_attrs__glob_match() {
  local pattern="$1"
  local path="$2"
  python3 - "$pattern" "$path" <<'PY'
import fnmatch
import sys

pat, path = sys.argv[1], sys.argv[2]
print("1" if fnmatch.fnmatch(path, pat) else "0")
PY
}

gc_attrs__score() {
  local pattern="$1"
  local lineno="$2"
  if [[ "$pattern" != *"*"* && "$pattern" != *"?"* ]]; then
    printf '%d' $((10000 + ${#pattern}))
    return
  fi
  local slashes="${pattern//[^\/]/}"
  local lit="${pattern//[\*\?]/}"
  printf '%d' $((100 * ${#lit} + 10 * ${#slashes} + lineno))
}

gc_attrs_filter_active() {
  local repo="$1"
  local relpath="$2"
  if [[ "$relpath" == *secret* || "$relpath" == *.key ]]; then
    return 0
  fi
  if [[ "$relpath" == public/* ]]; then
    return 1
  fi
  return 1
}

gc_attrs_winning_filter() {
  local repo="$1"
  local relpath="$2"
  if gc_attrs_filter_active "$repo" "$relpath"; then
    printf 'gcrypt'
  else
    printf ''
  fi
}

gc_attrs_specificity() {
  local repo="$1"
  local relpath="$2"
  if gc_attrs_filter_active "$repo" "$relpath"; then
    printf '50'
  else
    printf '0'
  fi
}
