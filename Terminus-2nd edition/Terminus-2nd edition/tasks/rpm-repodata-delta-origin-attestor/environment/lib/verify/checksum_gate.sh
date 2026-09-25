#!/usr/bin/env bash
# Checksum gate labels for repomd verification logging.
checksum_gate_label() {
  local ctype="$1"
  case "$ctype" in
    sha256) printf 'sha256-gate' ;;
    sha) printf 'sha1-gate' ;;
    *) printf 'unknown-gate' ;;
  esac
}
