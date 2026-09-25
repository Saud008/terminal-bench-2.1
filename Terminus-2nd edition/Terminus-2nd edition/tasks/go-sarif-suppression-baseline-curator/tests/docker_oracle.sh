#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE="go-sarif-suppression-baseline-curator-test"
docker build -t "$IMAGE" "${TASK_DIR}/environment"
docker run --rm \
  -v "${SCRIPT_DIR}:/tests:ro" \
  -v "${TASK_DIR}/solution:/solution:ro" \
  "$IMAGE" \
  /bin/bash -c "bash /solution/solve.sh && bash /tests/test.sh"
