#!/usr/bin/env bash
set -euo pipefail
TASK="$(cd "$(dirname "$0")/.." && pwd)"
docker run --rm \
  -v "$TASK/tests:/tests:ro" \
  -v "$TASK/solution:/solution:ro" \
  udp-reconciler-test bash -lc 'bash /solution/solve.sh && bash /tests/test.sh'
