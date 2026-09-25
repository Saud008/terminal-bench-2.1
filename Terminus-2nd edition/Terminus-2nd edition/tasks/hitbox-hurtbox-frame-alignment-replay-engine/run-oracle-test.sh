#!/usr/bin/env bash
set -euo pipefail
cd "/mnt/d/Terminus-2nd edition/Terminus-2nd edition"
docker run --rm \
  -v "$(pwd)/tasks/hitbox-hurtbox-frame-alignment-replay-engine/solution:/solution:ro" \
  -v "$(pwd)/tasks/hitbox-hurtbox-frame-alignment-replay-engine/tests:/tests:ro" \
  hitbox-replay-test bash -lc 'bash /solution/solve.sh && bash /tests/test.sh'
