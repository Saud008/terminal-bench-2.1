#!/usr/bin/env bash

normalize_d_tree() {
  local root="${D}"
  [ -d "${root}" ] || return 0
  find "${root}" -type d -exec chmod 0755 {} +
  find "${root}" -type f -exec chmod 0644 {} +
}
