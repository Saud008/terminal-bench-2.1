#!/usr/bin/env bash

APP_ROOT="${APP_ROOT:-/app}"
RULES_ROOT="${APP_ROOT}/fixtures/rules"
ACTIONS_ROOT="${APP_ROOT}/fixtures/actions"
CACHE_PATH="${APP_ROOT}/state/auth-cache.json"

die() {
  echo "pkctl: $*" >&2
  exit 1
}

tb3_root() {
  if [[ -n "${TB3_RULES_DIR:-}" && "${TB3_RULES_DIR}" == /* ]]; then
    echo "${TB3_RULES_DIR}"
    return
  fi
  echo ""
}

rules_dir_for() {
  local stack="$1"
  local tb3
  tb3="$(tb3_root)"
  if [[ -n "$tb3" ]]; then
    echo "${tb3}/rules/${stack}"
  else
    echo "${RULES_ROOT}/${stack}"
  fi
}

actions_dir() {
  local tb3
  tb3="$(tb3_root)"
  if [[ -n "$tb3" ]]; then
    echo "${tb3}/actions"
  else
    echo "${ACTIONS_ROOT}"
  fi
}
