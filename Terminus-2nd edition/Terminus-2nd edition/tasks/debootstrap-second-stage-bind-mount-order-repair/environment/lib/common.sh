#!/usr/bin/env bash

s2_trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

s2_json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  printf '%s' "$s"
}

s2_parent_target() {
  local t="$1"
  if [[ "$t" == "/" ]]; then
    return 1
  fi
  local parent="${t%/*}"
  [[ -z "$parent" ]] && parent="/"
  printf '%s' "$parent"
}
