#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${ROOT_DIR}/patches"
cp "${FILES}/patch_sql_resfetch.go" /app/internal/sqlpull/resfetch.go
cp "${FILES}/patch_cal_span.go" /app/internal/blackoutcal/span.go
cp "${FILES}/patch_tier_upgrade.go" /app/internal/tierlift/upgrade.go
cp "${FILES}/patch_guest_walkvictim.go" /app/internal/guestshield/walkvictim.go
cp "${FILES}/patch_guest_shield.go" /app/internal/guestshield/tier.go
cp "${FILES}/patch_rev_seal.go" /app/internal/revsnap/seal.go
cp "${FILES}/patch_scorewire.go" /app/internal/revsnap/scorewire.go
cp "${FILES}/patch_walkrank.go" /app/internal/costmin/walkrank.go
cp "${FILES}/patch_night_planqueue.go" /app/internal/nightopt/planqueue.go
cp "${FILES}/patch_night_walksort.go" /app/internal/nightopt/walksort.go
cp "${FILES}/patch_rev_digest.go" /app/internal/revsnap/digestwire.go
cp "${FILES}/patch_atlas_prep.go" /app/internal/walkreport/atlasprep.go
cp "${FILES}/patch_atlas_emit.go" /app/internal/walkreport/emit.go
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
