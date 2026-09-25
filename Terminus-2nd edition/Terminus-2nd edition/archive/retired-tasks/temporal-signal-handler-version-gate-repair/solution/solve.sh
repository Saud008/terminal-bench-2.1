#!/usr/bin/env bash
# Oracle: install golden Go modules and rebuild offline.
set -euo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
APP="/app"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_export.go" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_export.go not found" >&2
  exit 1
fi

echo "oracle: install golden modules from ${SOL_DIR}"
cp -f "${SOL_DIR}/golden_dispatch.go" "${APP}/internal/router/dispatch.go"
cp -f "${SOL_DIR}/golden_gate.go" "${APP}/internal/version/gate.go"
cp -f "${SOL_DIR}/golden_ack.go" "${APP}/internal/handler/ack.go"
cp -f "${SOL_DIR}/golden_dedup.go" "${APP}/internal/dedup/ledger.go"
cp -f "${SOL_DIR}/golden_clock.go" "${APP}/internal/heartbeat/clock.go"
cp -f "${SOL_DIR}/golden_export.go" "${APP}/internal/export/history.go"
cp -f "${SOL_DIR}/golden_staging.go" "${APP}/internal/staging/snapshot.go"

cd "${APP}"
go build -mod=readonly -o /usr/local/bin/temporal-signal-replay ./cmd/temporal-signal-replay
test -x /usr/local/bin/temporal-signal-replay

bash "${APP}/scripts/reset-state.sh"
temporal-signal-replay export \
  --scenario /app/fixtures/scenarios/09-ack-order-trap.json \
  --output /app/output/signal-history-export.json

echo "temporal-signal-replay oracle ready"
