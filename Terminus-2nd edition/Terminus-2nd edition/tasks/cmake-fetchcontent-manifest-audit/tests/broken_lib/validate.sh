#!/usr/bin/env bash
# Strict CMake list-file syntax checks.

validate_cmake_syntax() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "missing list file: $file" >&2
    return 2
  fi
  if ! grep -qi 'cmake_minimum_required' "$file"; then
    echo "missing cmake_minimum_required in $file" >&2
    return 2
  fi
  local opens closes
  opens=$(grep -o '(' "$file" | wc -l | tr -d ' ')
  closes=$(grep -o ')' "$file" | wc -l | tr -d ' ')
  if [[ "$opens" != "$closes" ]]; then
    echo "unbalanced parentheses in $file" >&2
    return 2
  fi
  return 0
}
