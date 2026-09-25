#!/usr/bin/env bash
set -euo pipefail

# rebuild-zonefrag-lib: refresh CLI permissions before behavioral pytest.
chmod +x /app/scripts/zonefrag /app/scripts/*.sh /app/lib/*.sh
install -m 0755 /app/scripts/zonefrag /usr/local/bin/zonefrag
