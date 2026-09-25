#!/usr/bin/env bash
# Rpath token handling for lt-canonicalize.

lt_dedupe_rpath() {
  local id="$1"
  local raw
  raw="$(lt_field "${id}" rpath)"
  LT_RPATH_DEDUP_REMOVED=0
  LT_RPATH_RESULT=()
  local -A seen
  local tok
  for tok in ${raw}; do
    [ -z "${tok}" ] && continue
    if [ -n "${seen[$tok]+x}" ]; then
      LT_RPATH_DEDUP_REMOVED=$((LT_RPATH_DEDUP_REMOVED + 1))
      continue
    fi
    seen["${tok}"]=1
    LT_RPATH_RESULT+=("${tok}")
  done
  if [ "${#LT_RPATH_RESULT[@]}" -gt 1 ]; then
    local old_ifs="${IFS}"
    IFS=$'\n'
    LT_RPATH_RESULT=($(printf '%s\n' "${LT_RPATH_RESULT[@]}" | LC_ALL=C sort))
    IFS="${old_ifs}"
  fi
}
