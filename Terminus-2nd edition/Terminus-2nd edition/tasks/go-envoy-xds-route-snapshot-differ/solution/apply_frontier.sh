#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +

cd /app
patch -p0 < "${ROOT_DIR}/patches/xsnap_scenario_bind.patch"
patch -p0 < "${ROOT_DIR}/patches/xsnap_pick_tier.patch"
patch -p0 < "${ROOT_DIR}/patches/xsnap_scale_slice.patch"
patch -p0 < "${ROOT_DIR}/patches/xsnap_tier_sort.patch"
patch -p0 < "${ROOT_DIR}/patches/xsnap_ref_bind.patch"
patch -p0 < "${ROOT_DIR}/patches/xsnap_persist_stage.patch"
patch -p0 < "${ROOT_DIR}/patches/xsnap_emit_chg.patch"

sed -i 's/gen.NormalizeRevision = gen.NormalizeRevision$/gen.NormalizeRevision = gen.NormalizeRevision + 1/' \
  /app/internal/normalizepass/normalize_core.go

test -s /app/internal/scenpair/scenario_bind.go
test -s /app/internal/chgledger/emit_chg.go

