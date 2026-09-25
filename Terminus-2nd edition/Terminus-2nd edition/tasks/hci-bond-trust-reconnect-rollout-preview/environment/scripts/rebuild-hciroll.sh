#!/usr/bin/env bash
# rebuild-hciroll.sh also runs via tests/conftest.py session autouse before pytest.
set -euo pipefail
find /app/lib/boltlane -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/lib/boltlane -name '*.sh' -exec chmod +x {} +
chmod +x /app/scripts/hciroll /app/scripts/reset-state.sh /app/scripts/rebuild-hciroll.sh
mkdir -p /app/bin /app/state /app/output /app/work
ln -sfn /app/scripts/hciroll /app/bin/hciroll
