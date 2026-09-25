#!/usr/bin/env bash
set -euo pipefail
cd "/mnt/d/Terminus-2nd edition/Terminus-2nd edition"
docker run --rm \
  -v "$(pwd)/tasks/fontconfig-charset-alias-substitution-dag-governor/solution:/solution:ro" \
  -v "$(pwd)/tasks/fontconfig-charset-alias-substitution-dag-governor/tests:/tests:ro" \
  -e AUTHOR_VALIDATION=1 \
  fc-gov-test bash -lc 'bash /solution/solve.sh && bash /tests/test.sh'
