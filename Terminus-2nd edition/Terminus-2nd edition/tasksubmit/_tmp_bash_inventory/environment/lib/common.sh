#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

tree_fingerprint() {
  local manifest="$1" root="$2"
  {
    cat "$manifest"
    find "$root" -type f | sort | while read -r f; do
      rel="${f#"$root"/}"
      printf '%s' "$rel"
      cat "$f"
    done
  } | sha256sum | awk '{print $1}'
}
