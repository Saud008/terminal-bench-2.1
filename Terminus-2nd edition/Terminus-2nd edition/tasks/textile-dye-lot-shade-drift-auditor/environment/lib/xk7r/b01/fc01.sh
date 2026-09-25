#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
CONFIG="${APP_ROOT}/config/shadedrift.json"
CORR_SNAP_DIR="${APP_ROOT}/state/shade-correlation"
REGISTRY="${APP_ROOT}/state/run-registry.jsonl"

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

read_policy() {
  cat "$CONFIG"
}
