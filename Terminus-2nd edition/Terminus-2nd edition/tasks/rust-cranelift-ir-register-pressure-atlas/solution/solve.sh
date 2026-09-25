#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd /app

patch -p1 -i "$ROOT_DIR/patches/residual_kernel/subtract.rs.patch"
patch -p1 -i "$ROOT_DIR/patches/quantize/micron_ev.rs.patch"
patch -p1 -i "$ROOT_DIR/patches/energy_order/sort.rs.patch"
patch -p1 -i "$ROOT_DIR/patches/coincidence_veto/apply.rs.patch"
patch -p1 -i "$ROOT_DIR/patches/occupancy_scan/peak.rs.patch"
patch -p1 -i "$ROOT_DIR/patches/fluence_ledger/accrue.rs.patch"
patch -p1 -i "$ROOT_DIR/patches/closure_rank/order.rs.patch"
patch -p1 -i "$ROOT_DIR/patches/digest_line/seal.rs.patch"

/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/fluxpress /app/bin/fluxpress
bash /app/scripts/reset-workspace.sh
test -x /app/bin/fluxpress
echo "rust-cranelift-ir-register-pressure-atlas oracle ready"
