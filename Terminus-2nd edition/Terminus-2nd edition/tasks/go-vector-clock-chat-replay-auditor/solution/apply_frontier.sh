#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +

cp "${ROOT_DIR}/files/lamportmesh_merge.go" /app/internal/lamportmesh/merge.go
cp "${ROOT_DIR}/files/modgate_precedence.go" /app/internal/modgate/precedence.go
cp "${ROOT_DIR}/files/silencewin_window.go" /app/internal/silencewin/window.go
cp "${ROOT_DIR}/files/receiptcollapse_suppress.go" /app/internal/receiptcollapse/suppress.go
cp "${ROOT_DIR}/files/deliveryproof_validate.go" /app/internal/deliveryproof/validate.go
cp "${ROOT_DIR}/files/roombind_shard_pull.go" /app/internal/roombind/shard_pull.go
cp "${ROOT_DIR}/files/chronicle_timeline_seal.go" /app/internal/chronicle/timeline_seal.go

sed -i 's/return defaultMaxGap + bias + 1/return defaultMaxGap + bias/' /app/internal/clockjump/detect.go
sed -i 's/gen.ReconcileRevision = gen.ReconcileRevision$/gen.ReconcileRevision = gen.ReconcileRevision + 1/' \
  /app/internal/casaudit/reconcile_core.go

test -s /app/internal/lamportmesh/merge.go
test -s /app/internal/modgate/precedence.go
test -s /app/internal/silencewin/window.go
test -s /app/internal/receiptcollapse/suppress.go
test -s /app/internal/deliveryproof/validate.go
test -s /app/internal/roombind/shard_pull.go
test -s /app/internal/chronicle/timeline_seal.go
test -s /app/internal/clockjump/detect.go
test -s /app/internal/casaudit/reconcile_core.go
