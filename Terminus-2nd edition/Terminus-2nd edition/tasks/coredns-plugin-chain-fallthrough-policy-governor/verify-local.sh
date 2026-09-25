#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
IMAGE="coredns-plugin-chain-fallthrough-policy-governor:local"

docker build -t "$IMAGE" "$ROOT/environment"

echo "=== NOP (expect reward 0) ==="
docker run --rm -v "$ROOT/tests:/tests:ro" "$IMAGE" bash -lc 'bash /tests/test.sh; cat /logs/verifier/reward.txt'

echo "=== Oracle (expect reward 1) ==="
docker run --rm \
  -v "$ROOT/solution:/solution:ro" \
  -v "$ROOT/tests:/tests:ro" \
  "$IMAGE" bash -lc 'bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'

echo "Done. Pack with: python3 package-submit.py"
