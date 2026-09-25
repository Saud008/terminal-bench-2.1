#!/usr/bin/env bash
set -euo pipefail

OUTPUT="/app/output"
TOUCH="${OUTPUT}/.parser-touch"

ensure_output_dir() {
  mkdir -p "${OUTPUT}"
}

reset_output() {
  ensure_output_dir
  : > "${TOUCH}"
}
