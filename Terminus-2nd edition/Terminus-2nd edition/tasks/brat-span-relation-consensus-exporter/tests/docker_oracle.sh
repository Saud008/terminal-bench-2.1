#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
IMAGE="bratctl-test"
docker build -t "$IMAGE" "$REPO/tasks/brat-span-relation-consensus-exporter/environment"
docker run --rm \
  -v "$REPO/tasks/brat-span-relation-consensus-exporter/tests:/tests:ro" \
  -v "$REPO/tasks/brat-span-relation-consensus-exporter/solution:/solution:ro" \
  "$IMAGE" \
  /bin/bash -c "bash /solution/solve.sh && bash /tests/test.sh"
