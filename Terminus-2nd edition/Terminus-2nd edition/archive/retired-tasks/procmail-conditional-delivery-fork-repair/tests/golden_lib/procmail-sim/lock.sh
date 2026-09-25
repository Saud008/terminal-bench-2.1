#!/usr/bin/env bash
# Lockfile path helpers for recipe blocks.
# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

declare -A PM_ACTIVE_LOCKS=()

lock_path_for() {
  local scope="$1"
  local name="$2"
  printf '%s/%s/%s' "$LOCK_ROOT" "$scope" "$name"
}

lock_try_acquire() {
  local path="$1"
  [[ -z "${PM_ACTIVE_LOCKS[$path]:-}" ]] || return 1
  PM_ACTIVE_LOCKS["$path"]=1
  mkdir -p "$(dirname "$path")"
  : >"$path"
  return 0
}

lock_release() {
  local path="$1"
  unset 'PM_ACTIVE_LOCKS[$path]'
}
