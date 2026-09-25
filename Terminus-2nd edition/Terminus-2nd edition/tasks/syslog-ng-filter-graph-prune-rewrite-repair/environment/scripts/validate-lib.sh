#!/usr/bin/env bash
set -euo pipefail

required=(
  /app/lib/common.sh
  /app/lib/boolean.sh
  /app/lib/prune.sh
  /app/lib/branch.sh
  /app/lib/cache.sh
  /app/lib/facility_gate.sh
  /app/lib/rewrite.sh
  /app/lib/export.sh
  /app/lib/staging.sh
  /app/lib/replay.sh
)

for f in "${required[@]}"; do
  [ -f "$f" ] || {
    echo "missing required library: $f" >&2
    exit 1
  }
done
