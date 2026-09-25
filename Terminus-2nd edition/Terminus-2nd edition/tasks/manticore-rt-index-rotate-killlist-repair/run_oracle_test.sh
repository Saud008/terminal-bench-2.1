#!/usr/bin/env bash
set -euo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"

echo "=== M1 /solution ==="
docker run --rm --network=none \
  -v "${TASK}/steps/milestone_1/solution:/solution:ro" \
  -v "${TASK}/steps/milestone_1/tests:/tests:ro" \
  mantidx-test bash -lc 'set -euo pipefail; bash /solution/solve.sh; bash /tests/test.sh; test "$(cat /logs/verifier/reward.txt)" = "1"'

echo "=== M1 /oracle/solution ==="
docker run --rm --network=none \
  -v "${TASK}/steps/milestone_1/solution:/oracle/solution:ro" \
  -v "${TASK}/steps/milestone_1/tests:/tests:ro" \
  mantidx-test bash -lc 'set -euo pipefail; bash /oracle/solution/solve.sh; bash /tests/test.sh; test "$(cat /logs/verifier/reward.txt)" = "1"'

echo "=== M2 /solution ==="
docker run --rm --network=none \
  -v "${TASK}/steps/milestone_2/solution:/solution:ro" \
  -v "${TASK}/steps/milestone_2/tests:/tests:ro" \
  mantidx-test bash -lc 'set -euo pipefail; bash /solution/solve.sh; bash /tests/test.sh; test "$(cat /logs/verifier/reward.txt)" = "1"'

echo "=== M2 /task/steps/milestone_2/solution ==="
docker run --rm --network=none \
  -v "${TASK}/steps/milestone_2/solution:/task/steps/milestone_2/solution:ro" \
  -v "${TASK}/steps/milestone_2/tests:/tests:ro" \
  mantidx-test bash -lc 'set -euo pipefail; bash /task/steps/milestone_2/solution/solve.sh; bash /tests/test.sh; test "$(cat /logs/verifier/reward.txt)" = "1"'

echo "ALL ORACLE CHECKS PASSED"
