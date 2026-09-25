#!/usr/bin/env bash
# Shared helpers for gcrypt-filter.

gc__trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

gc__require_dir() {
  local d="$1"
  [[ -d "$d" ]] || {
    echo "gcrypt-filter: not a directory: $d" >&2
    return 1
  }
}

gc__require_relpath() {
  local p="$1"
  [[ -n "$p" ]] || {
    echo "gcrypt-filter: empty path" >&2
    return 1
  }
  [[ "$p" != /* ]] || {
    echo "gcrypt-filter: path must be relative: $p" >&2
    return 1
  }
}

gc__read_stdin() {
  cat
}

gc__stdin_slurp_file() {
  local dest="$1"
  cat > "$dest"
}
