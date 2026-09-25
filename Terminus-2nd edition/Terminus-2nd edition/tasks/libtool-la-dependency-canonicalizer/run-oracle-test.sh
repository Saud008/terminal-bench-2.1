#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
TASK="$(cd "$(dirname "$0")" && pwd)"
docker run --rm \
  -v "${TASK}/solution:/solution:ro" \
  -v "${TASK}/tests:/tests:ro" \
  lt-canonicalizer-test \
  bash -lc 'bash /solution/solve.sh && bash /tests/test.sh'
