#!/usr/bin/env bash
# Library path resolution and static/shared name merge for lt-canonicalize.

lt_resolve_dir() {
  local id="$1"
  LT_RESOLVE_DIR="$(lt_field "${id}" libdir)"
}

lt_merge_names() {
  local id="$1"
  local dlname old libnames
  dlname="$(lt_field "${id}" dlname)"
  old="$(lt_field "${id}" old_library)"
  libnames="$(lt_field "${id}" library_names)"
  LT_SHARED_NAME="${dlname}"
  LT_STATIC_FALLBACK=""
  if [ -n "${old}" ]; then
    LT_STATIC_FALLBACK="${old}"
    if [ -n "${libnames}" ]; then
      LT_SHARED_NAME="${libnames%% *}"
    fi
  fi
}

lt_installed_flag() {
  local id="$1"
  local v
  v="$(lt_field "${id}" installed)"
  if [ "${v}" = "yes" ]; then
    LT_INSTALLED=true
  else
    LT_INSTALLED=false
  fi
}
