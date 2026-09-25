#!/usr/bin/env bash

compile_zone_tree() {
  local tree="$1"
  local seed="$2"
  local out="$3"
  local reload="${4:-0}"
  export_compile "$tree" "$seed" "$out" "$reload"
}
