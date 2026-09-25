#!/usr/bin/env bash
# Cycle detection and edge removal for lt-canonicalize.

lt_break_cycles() {
  LT_BROKEN=()
  LT_CYCLES_BROKEN=0
  local -A removed
  while true; do
    local found=0
    local start
    for start in "${LT_IDS[@]}"; do
      LT_VIS=()
      LT_STACK=()
      if _lt_cycle_dfs "${start}" "${start}"; then
        echo "fatal cycle involving ${start}" >&2
        return 1
      fi
    done
    break
  done
  return 0
}

_lt_cycle_dfs() {
  local node="$1"
  local start="$1"
  local dep
  LT_VIS+=("${node}")
  LT_STACK+=("${node}")
  while IFS= read -r dep; do
    [ -z "${dep}" ] && continue
    if _lt_in_stack "${dep}"; then
      return 0
    fi
    if _lt_list_has "${dep}" "${LT_VIS[@]}"; then
      continue
    fi
    if _lt_cycle_dfs "${dep}"; then
      return 0
    fi
  done < <(lt_direct_deps "${node}")
  return 1
}

_lt_in_stack() {
  local needle="$1"
  local x
  for x in "${LT_STACK[@]}"; do
    [ "${x}" = "${needle}" ] && return 0
  done
  return 1
}

_lt_list_has() {
  local needle="$1"
  shift
  local x
  for x in "$@"; do
    [ "${x}" = "${needle}" ] && return 0
  done
  return 1
}

lt_edge_removed() {
  local from="$1"
  local to="$2"
  local key="${from}/${to}"
  local edge
  for edge in "${LT_BROKEN[@]}"; do
    [ "${edge}" = "${key}" ] && return 0
  done
  return 1
}
