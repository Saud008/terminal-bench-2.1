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

gc_staging_remove() {
  local relpath="$1"
  local dest
  dest="$(gc_staging_path_for "$relpath")"
  rm -f "$dest"
}

gc_staging_clear_all() {
  rm -rf "${GC_STAGING_ROOT:?}/"*
}
