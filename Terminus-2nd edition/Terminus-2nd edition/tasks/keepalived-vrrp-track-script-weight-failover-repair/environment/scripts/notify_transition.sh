#!/usr/bin/env bash
set -euo pipefail
# Simulated notify hook — writes notify.done when transition handling completes.
MARKER="/app/state/notify.done"
mkdir -p /app/state
echo "notify_complete" > "${MARKER}"
