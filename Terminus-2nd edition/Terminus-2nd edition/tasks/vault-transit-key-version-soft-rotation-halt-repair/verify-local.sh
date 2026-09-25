#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
IMAGE="${TRANSIT_TEST_IMAGE:-transit-task-test}"

echo "=== oracle ==="
docker run --rm \
  -v "${ROOT}/tests:/tests:ro" \
  -v "${ROOT}/solution:/solution:ro" \
  "${IMAGE}" \
  bash -c 'for f in /solution/*.sh; do [ -f "$f" ] && sed -i "s/\r$//" "$f" 2>/dev/null || true; done; bash /solution/solve.sh && TEST_DIR=/tests bash /tests/test.sh && cat /logs/verifier/reward.txt'

echo "=== nop ==="
docker run --rm \
  -v "${ROOT}/tests:/tests:ro" \
  "${IMAGE}" \
  bash -c 'TEST_DIR=/tests bash /tests/test.sh && cat /logs/verifier/reward.txt'
