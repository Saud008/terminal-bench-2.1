#!/usr/bin/env bash
set -euo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "${TASK}/steps/milestone_1/solution/fixed"
mkdir -p "${TASK}/steps/milestone_2/solution/fixed"

M1_CID=$(docker create \
  -v "${TASK}/steps/milestone_1/solution:/solution:ro" \
  mantidx-test bash -lc 'bash /solution/solve1.sh')
docker start -a "${M1_CID}"
docker cp "${M1_CID}:/usr/local/bin/mantidx" "${TASK}/steps/milestone_1/solution/fixed/mantidx"
docker rm "${M1_CID}" >/dev/null

M2_CID=$(docker create \
  -v "${TASK}/steps/milestone_2/solution:/solution:ro" \
  mantidx-test bash -lc 'bash /solution/solve2.sh')
docker start -a "${M2_CID}"
docker cp "${M2_CID}:/usr/local/bin/mantidx" "${TASK}/steps/milestone_2/solution/fixed/mantidx"
docker rm "${M2_CID}" >/dev/null

chmod +x "${TASK}/steps/milestone_1/solution/fixed/mantidx"
chmod +x "${TASK}/steps/milestone_2/solution/fixed/mantidx"
ls -la "${TASK}/steps/milestone_1/solution/fixed/mantidx" "${TASK}/steps/milestone_2/solution/fixed/mantidx"
