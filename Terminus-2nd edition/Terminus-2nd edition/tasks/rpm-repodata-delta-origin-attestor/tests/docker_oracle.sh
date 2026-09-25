#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
IMAGE="rpm-repo-attest-test"
docker build -t "$IMAGE" "$REPO/tasks/rpm-repodata-delta-origin-attestor/environment"
docker run --rm \
  -v "$REPO/tasks/rpm-repodata-delta-origin-attestor/tests:/tests:ro" \
  -v "$REPO/tasks/rpm-repodata-delta-origin-attestor/solution:/solution:ro" \
  "$IMAGE" \
  /bin/bash -c "bash /solution/solve.sh && bash /tests/test.sh"
