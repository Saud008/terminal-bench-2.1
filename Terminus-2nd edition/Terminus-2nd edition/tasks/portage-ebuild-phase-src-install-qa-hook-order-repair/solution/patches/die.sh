#!/usr/bin/env bash

ebuild_die() {
  local msg="$1"
  echo "!!! ${msg}" >&2
  return 1
}
