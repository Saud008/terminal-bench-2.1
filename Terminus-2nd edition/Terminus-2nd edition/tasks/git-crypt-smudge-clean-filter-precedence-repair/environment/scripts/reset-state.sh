#!/usr/bin/env bash
set -euo pipefail

rm -rf /app/state/staging
mkdir -p /app/state/staging /app/output
rm -f /app/output/encrypted-manifest.json
