#!/usr/bin/env bash
# rebuild-lib: refresh execute bits on stage2 bash modules before verifier pytest.
set -euo pipefail
chmod +x /app/lib/*.sh /app/bin/stage2-audit /app/scripts/*.sh
