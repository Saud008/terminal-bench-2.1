#!/usr/bin/env bash
set -euo pipefail

CONFIG="${PAMTRACE_CONFIG:-/app/config/pamtrace.json}"
LEDGER="$(jq -r '.ledger_path' "$CONFIG")"
WORK_DIR="$(jq -r '.work_dir' "$CONFIG")"
SCENARIO_DIR="$(jq -r '.scenario_dir' "$CONFIG")"
if [[ -n "${PAMTRACE_SCENARIO_OVERRIDE:-}" ]]; then
  SCENARIO_DIR="${PAMTRACE_SCENARIO_OVERRIDE}/fixtures/scenarios"
fi

sha256_hex() {
  printf '%s' "$1" | sha256sum | awk '{print $1}'
}
