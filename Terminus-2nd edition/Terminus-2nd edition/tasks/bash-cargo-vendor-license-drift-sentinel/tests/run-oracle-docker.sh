#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker run --rm \
  -v "${TASK_DIR}/solution:/solution" \
  -v "${TASK_DIR}/tests:/tests:ro" \
  cvls-test \
  bash -c 'sed -i "s/\r$//" /solution/solve.sh /solution/oracle/*.sh /solution/files/*.sh 2>/dev/null || true; bash /solution/solve.sh && bash /tests/test.sh'
