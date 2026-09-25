#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
docker run --rm \
  -v "$REPO/tasks/git-packfile-delta-chain-packctl/tests:/tests:ro" \
  packctl-test \
  /bin/bash /tests/test.sh
