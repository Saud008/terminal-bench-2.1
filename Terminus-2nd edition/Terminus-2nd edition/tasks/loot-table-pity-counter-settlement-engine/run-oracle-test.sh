#!/usr/bin/env bash
set -euo pipefail
cd "/mnt/d/Terminus-2nd edition/Terminus-2nd edition"
docker run --rm \
  -v "$(pwd)/tasks/loot-table-pity-counter-settlement-engine/solution:/solution:ro" \
  -v "$(pwd)/tasks/loot-table-pity-counter-settlement-engine/tests:/tests:ro" \
  lootsettle-test bash -lc 'bash /solution/solve.sh && bash /tests/test.sh'
