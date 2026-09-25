#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/audit.db /app/state/cose-stage.json
rm -f /app/output/chain-manifest.json
mkdir -p /app/state /app/output
