#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${ROOT_DIR}/patches"
cp "${FILES}/patch_suspend_window.go" /app/internal/patronbar/cal.go
cp "${FILES}/patch_tier_sort.go" /app/internal/priqueue/sort.go
cp "${FILES}/patch_copy_select.go" /app/internal/branchsel/select.go
cp "${FILES}/patch_rollup_fingerprint.go" /app/internal/snaprollup/digestwire.go
cp "${FILES}/patch_idem_stamp.go" /app/internal/passmark/seal.go
cp "${FILES}/patch_publish_atlas.go" /app/internal/atlasledger/ledgeremit.go
sed -i 's/passmark.RunStamp(digest)/passmark.RunStamp(scenario, digest)/' /app/internal/reconcile/fairness.go
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
