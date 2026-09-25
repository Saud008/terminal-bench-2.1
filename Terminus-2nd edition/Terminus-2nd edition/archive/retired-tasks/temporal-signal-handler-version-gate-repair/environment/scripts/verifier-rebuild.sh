#!/usr/bin/env bash
set -euo pipefail

BROKEN="/opt/verifier-broken-temporal"
APP="/app/internal"

cp "${BROKEN}/dispatch.go" "${APP}/router/dispatch.go"
cp "${BROKEN}/gate.go" "${APP}/version/gate.go"
cp "${BROKEN}/ack.go" "${APP}/handler/ack.go"
cp "${BROKEN}/dedup.go" "${APP}/dedup/ledger.go"
cp "${BROKEN}/clock.go" "${APP}/heartbeat/clock.go"
cp "${BROKEN}/export.go" "${APP}/export/history.go"
cp "${BROKEN}/staging.go" "${APP}/staging/snapshot.go"

go build -mod=readonly -o /usr/local/bin/temporal-signal-replay ./cmd/temporal-signal-replay
