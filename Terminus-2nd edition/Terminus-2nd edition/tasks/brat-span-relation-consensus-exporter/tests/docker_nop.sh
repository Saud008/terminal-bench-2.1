#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
IMAGE="bratctl-test"
docker build -t "$IMAGE" "$REPO/tasks/brat-span-relation-consensus-exporter/environment" >/dev/null
reward="$(docker run --rm \
  -v "$REPO/tasks/brat-span-relation-consensus-exporter/tests:/tests:ro" \
  "$IMAGE" \
  /bin/bash -c "bash /tests/test.sh >/dev/null 2>&1; cat /logs/verifier/reward.txt")"
if [[ "$reward" == "0" ]]; then
  exit 0
fi
echo "NOP expected reward 0 but got: $reward" >&2
exit 1
