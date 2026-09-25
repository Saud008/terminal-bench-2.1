#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_backoff.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden sources not found" >&2; exit 1; }

cp -f "${SOL}/golden_backoff.go" /app/internal/scheduler/backoff.go
cp -f "${SOL}/golden_queue.go" /app/internal/scheduler/queue.go
cp -f "${SOL}/golden_heartbeat.go" /app/internal/scheduler/heartbeat.go
cp -f "${SOL}/golden_poison.go" /app/internal/scheduler/poison.go
cp -f "${SOL}/golden_store.go" /app/internal/store/store.go

bash /app/scripts/build-cli.sh
