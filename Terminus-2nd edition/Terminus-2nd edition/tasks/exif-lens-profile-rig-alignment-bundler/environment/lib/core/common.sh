#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
STAGING_PATH="${STAGING_PATH:-/app/state/capture-staging.json}"
STAGING_SEQ_PATH="${STAGING_SEQ_PATH:-/app/state/staging-seq.json}"
ALIGN_GEN_PATH="${ALIGN_GEN_PATH:-/app/state/align-generation.json}"
BUNDLE_PATH="${BUNDLE_PATH:-/app/output/bundle-manifest.json}"
REJECTED_PATH="${REJECTED_PATH:-/app/output/rejected-captures.jsonl}"
CAL_ERROR_LIMIT="${CAL_ERROR_LIMIT:-0.5}"

die() {
  echo "rigbundle: $*" >&2
  exit 1
}

require_file() {
  [ -f "$1" ] || die "missing file: $1"
}

require_dir() {
  [ -d "$1" ] || die "missing directory: $1"
}

fixture_root() {
  if [ -n "${TB3_FIXTURE_DIR:-}" ]; then
    echo "${TB3_FIXTURE_DIR}"
  else
    echo "${APP_ROOT}/fixtures"
  fi
}
