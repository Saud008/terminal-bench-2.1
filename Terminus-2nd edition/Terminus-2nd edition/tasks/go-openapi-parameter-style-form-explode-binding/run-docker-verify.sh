#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "$0")" && pwd)"
docker run --rm \
  -e TEST_DIR=/tests \
  -v "${TASK_ROOT}/solution:/solution:ro" \
  -v "${TASK_ROOT}/tests:/tests:ro" \
  paramgate-test \
  bash -lc 'ls -la /tests/ && bash /solution/solve.sh && bash /tests/test.sh && cat /logs/verifier/reward.txt'
