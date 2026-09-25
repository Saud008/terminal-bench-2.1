#!/usr/bin/env bash
set -euo pipefail
ROOT="/app"
rm -rf "${ROOT}/state/locks" "${ROOT}/state/delivery-snapshot.json" "${ROOT}/output/procmail-audit.json"
mkdir -p "${ROOT}/state/locks" "${ROOT}/output" "${ROOT}/state"
echo "reset ok"
