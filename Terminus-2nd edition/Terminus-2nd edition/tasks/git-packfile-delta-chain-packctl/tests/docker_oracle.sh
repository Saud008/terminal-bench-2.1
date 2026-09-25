#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
docker run --rm \
  -v "$REPO/tasks/git-packfile-delta-chain-packctl/tests:/tests:ro" \
  -v "$REPO/tasks/git-packfile-delta-chain-packctl/solution:/solution:ro" \
  packctl-test \
  /bin/bash -c "bash /solution/solve.sh && bash /tests/test.sh"
