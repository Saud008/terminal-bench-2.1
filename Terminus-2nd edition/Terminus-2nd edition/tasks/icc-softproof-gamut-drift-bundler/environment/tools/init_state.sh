#!/usr/bin/env bash
set -euo pipefail
mkdir -p /app/output /app/state
echo '{"runs":[]}' > /app/state/run-registry.json
