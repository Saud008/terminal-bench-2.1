#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
IMAGE="mdtable-audit"

docker build -t "${IMAGE}" "${ROOT}/environment"

echo "=== Oracle ==="
docker run --rm \
  -v "${ROOT}/solution:/solution" \
  -v "${ROOT}/tests:/tests" \
  "${IMAGE}" bash -c 'bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'

echo "=== NOP ==="
docker run --rm \
  -v "${ROOT}/tests:/tests" \
  "${IMAGE}" bash -c 'bash /tests/test.sh; cat /logs/verifier/reward.txt'

python3 "${ROOT}/package-submit.py"
