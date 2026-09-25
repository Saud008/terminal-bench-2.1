#!/usr/bin/env bash
# Resolve .gcrypt key material relative to repo root.

# shellcheck source=gc_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/gc_common.sh"

gc_key_load() {
  local repo="$1"
  local keyfile="${repo}/.gcrypt/keys/default"
  [[ -f "$keyfile" ]] || {
    echo "gcrypt-filter: missing key file: $keyfile" >&2
    return 1
  }
  GC_KEY_ID=""
  GC_KEY_MATERIAL=""
  while IFS='=' read -r k v; do
    k="$(gc__trim "$k")"
    v="$(gc__trim "$v")"
    case "$k" in
      key_id) GC_KEY_ID="$v" ;;
      material) GC_KEY_MATERIAL="$v" ;;
    esac
  done < "$keyfile"
  [[ -n "$GC_KEY_ID" && -n "$GC_KEY_MATERIAL" ]]
}

gc_key_id() {
  printf '%s' "$GC_KEY_ID"
}
