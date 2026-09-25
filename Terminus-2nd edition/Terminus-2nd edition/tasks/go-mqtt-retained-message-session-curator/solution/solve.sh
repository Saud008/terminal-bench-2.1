#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app
bash "${ROOT_DIR}/apply_frontier.sh"
python3 /app/fixtures/build_fixtures.py
MQTT_HIDDEN_ROOT=/opt/verifier-fixtures/mqttsessctl python3 /app/fixtures/build_fixtures.py
bash /app/scripts/verifier-rebuild.sh
test -x /app/bin/mqttsessctl
echo "mqttsessctl oracle ready"
