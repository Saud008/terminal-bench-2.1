#!/usr/bin/env bash
# Path containment helper used by optional tooling around src_install.
path_guard_under() {
  local root="$1"
  local candidate="$2"
  case "${candidate}" in
    "${root}"|"${root}"/*) return 0 ;;
    *) return 1 ;;
  esac
}
