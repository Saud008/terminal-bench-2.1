#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${ROOT_DIR}/files"
cp "${FILES}/tick_patch_expirygate.go" /app/internal/expirygate/boundary.go
cp "${FILES}/tick_patch_captureorder.go" /app/internal/captureorder/sort.go
cp "${FILES}/tick_patch_rowguard.go" /app/internal/rowguard/block.go
cp "${FILES}/tick_patch_accessfloor.go" /app/internal/accessfloor/inventory.go
cp "${FILES}/tick_patch_holddigest.go" /app/internal/holddigest/fingerprint.go
cp "${FILES}/tick_patch_passseal.go" /app/internal/passseal/stamp.go
cp "${FILES}/tick_patch_seatledger.go" /app/internal/seatledger/status.go
cp "${FILES}/tick_patch_mapapply.go" /app/internal/mapapply/map.go
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
