#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${ROOT_DIR}/files"
cp "${FILES_DIR}/frontier_cycle_window.go" /app/internal/cyclewindow/window.go
cp "${FILES_DIR}/frontier_proration_bps.go" /app/internal/prorateengine/prorate.go
cp "${FILES_DIR}/frontier_coupon_rank.go" /app/internal/couponstack/stack.go
cp "${FILES_DIR}/frontier_meter_carry.go" /app/internal/metercarry/carry.go
cp "${FILES_DIR}/frontier_anchor_shift.go" /app/internal/anchorsync/anchor.go
cp "${FILES_DIR}/frontier_buffer_snap.go" /app/internal/entsnap/sync.go
cp "${FILES_DIR}/frontier_entitlement_pass.go" /app/internal/entitlementrun/run.go
cp "${FILES_DIR}/frontier_invoice_publish.go" /app/internal/invoicepub/publish.go
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
