#!/usr/bin/env bash
set -euo pipefail
ROOT="/mnt/d/Terminus-2nd edition/Terminus-2nd edition"
cd "${ROOT}"
IMAGE=borg-prune-test
TASK=tasks/borg-prune-retention-policy-simulator

echo "=== NOP (broken baseline) ==="
set +e
docker run --rm \
  -v "${ROOT}/${TASK}/tests:/tests:ro" \
  "${IMAGE}" bash -lc 'bash /tests/test.sh'
nop_rc=$?
set -e
echo "NOP exit: ${nop_rc}"

echo "=== Oracle (solution) ==="
docker run --rm \
  -v "${ROOT}/${TASK}/solution:/solution:ro" \
  -v "${ROOT}/${TASK}/tests:/tests:ro" \
  "${IMAGE}" bash -lc 'bash /solution/solve.sh && bash /tests/test.sh'
echo "Oracle exit: 0"
