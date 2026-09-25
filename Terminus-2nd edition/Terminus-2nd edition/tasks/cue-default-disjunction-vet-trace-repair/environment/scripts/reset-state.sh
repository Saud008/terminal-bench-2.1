#!/usr/bin/env bash
set -euo pipefail
mkdir -p /app/output /app/state/eval-snapshots
rm -f /app/output/*.json 2>/dev/null || true
rm -f /app/state/eval-snapshots/*.json 2>/dev/null || true
