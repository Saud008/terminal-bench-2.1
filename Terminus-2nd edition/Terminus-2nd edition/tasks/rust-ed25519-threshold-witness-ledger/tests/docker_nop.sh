#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE="twctl-witness-ledger-test"
docker build -t "$IMAGE" "${TASK_DIR}/environment"
docker run --rm \
  -v "${SCRIPT_DIR}:/tests:ro" \
  "$IMAGE" \
  /bin/bash -c "bash /tests/test.sh"
