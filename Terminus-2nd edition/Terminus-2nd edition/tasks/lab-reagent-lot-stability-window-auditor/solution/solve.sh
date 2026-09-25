#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd /app

patch -p1 < "$ROOT/patches/correlation_store/artifact_store.rs.patch"
patch -p1 < "$ROOT/patches/provenance_digest/digest_line.rs.patch"
patch -p1 < "$ROOT/patches/assay_coupling/lot_resolver.rs.patch"
patch -p1 < "$ROOT/patches/chrono_integral/excursion_kernel.rs.patch"
patch -p1 < "$ROOT/patches/calendar_extend/calendar_roll.rs.patch"
patch -p1 < "$ROOT/patches/closure_rank/rank_lots.rs.patch"

/usr/local/cargo/bin/cargo build --release
install -m 0755 /app/target/release/reagentwin /app/bin/reagentwin
bash /app/scripts/reset-workspace.sh
test -x /app/bin/reagentwin
echo "lab-reagent-lot-stability-window-auditor oracle ready"
