#!/usr/bin/env bash
set -euo pipefail
mkdir -p /app/state /app/output
if [[ ! -f /app/state/run-registry.json ]]; then
  echo '{"runs":[]}' > /app/state/run-registry.json
fi
