#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/work/tree /app/work/state.json
mkdir -p /app/work/tree /app/output
rm -f /app/output/*.json
