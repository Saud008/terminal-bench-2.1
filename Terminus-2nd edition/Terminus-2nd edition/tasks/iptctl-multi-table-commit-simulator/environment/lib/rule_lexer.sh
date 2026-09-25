#!/usr/bin/env bash

restore_exists() {
  [[ -f "$1" ]]
}

parse_restore_file() {
  local out="$2"
  printf '{}\n' >"$out"
}
