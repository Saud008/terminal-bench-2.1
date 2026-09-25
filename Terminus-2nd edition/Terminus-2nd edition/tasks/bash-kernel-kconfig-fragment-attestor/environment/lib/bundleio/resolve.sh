#!/usr/bin/env bash
set -euo pipefail

# Bundle path resolution helpers (used by compile-stage).
APP_ROOT="${APP_ROOT:-/app}"

resolve_bundle_root() {
  echo "${TB3_BUNDLE_ROOT:-${APP_ROOT}/fixtures/bundles}"
}

resolve_bundle_base() {
  local bundle="$1"
  local root
  root=$(resolve_bundle_root)
  echo "${root}/${bundle}"
}

load_bundle_json() {
  local bundle="$1"
  cat "$(resolve_bundle_base "$bundle")/bundle.json"
}
