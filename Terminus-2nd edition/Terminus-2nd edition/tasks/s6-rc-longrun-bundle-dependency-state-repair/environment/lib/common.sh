#!/usr/bin/env bash
set -euo pipefail

OUTPUT="/app/output"
STATE="/app/state"
TOUCH="${OUTPUT}/.parser-touch"

ensure_output_dir() {
  mkdir -p "${OUTPUT}"
}

reset_output() {
  ensure_output_dir
  : > "${TOUCH}"
}

reset_state() {
  rm -rf "${STATE}/rc" "${STATE}/staging.json" "${STATE}/applied.json" "${STATE}/transition-log.json"
  mkdir -p "${STATE}/rc"
}
