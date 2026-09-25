#!/usr/bin/env bash
# Staging area writes for smudge --staging.

# shellcheck source=gc_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/gc_common.sh"

GC_STAGING_ROOT="/app/state/staging"

gc_staging_path_for() {
  local relpath="$1"
  printf '%s/%s' "$GC_STAGING_ROOT" "$relpath"
}

gc_staging_write() {
  local relpath="$1"
  local content="$2"
  local dest
  dest="$(gc_staging_path_for "$relpath")"
  mkdir -p "$(dirname "$dest")"
  printf '%s' "$content" > "$dest"
}

gc_staging_prepare() {
  local relpath="$1"
  gc_staging_remove "$relpath"
}

gc_staging_commit() {
  local relpath="$1"
  local src_file="$2"
  local dest tmp
  dest="$(gc_staging_path_for "$relpath")"
  mkdir -p "$(dirname "$dest")"
  tmp="${dest}.tmp.$$"
  cp "$src_file" "$tmp"
  mv -f "$tmp" "$dest"
}

gc_staging_rollback() {
  gc_staging_remove "$1"
}

gc_staging_remove() {
  local relpath="$1"
  local dest
  dest="$(gc_staging_path_for "$relpath")"
  rm -f "$dest" "${dest}.tmp."*
}

gc_staging_clear_all() {
  rm -rf "${GC_STAGING_ROOT:?}/"*
}
