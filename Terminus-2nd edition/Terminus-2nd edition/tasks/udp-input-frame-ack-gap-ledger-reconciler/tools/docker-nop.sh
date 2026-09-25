#!/usr/bin/env bash
set -euo pipefail
TASK="$(cd "$(dirname "$0")/.." && pwd)"
docker run --rm \
  -v "$TASK/tests:/tests:ro" \
  udp-reconciler-test bash -lc 'bash /tests/test.sh; echo EXIT=$?'
