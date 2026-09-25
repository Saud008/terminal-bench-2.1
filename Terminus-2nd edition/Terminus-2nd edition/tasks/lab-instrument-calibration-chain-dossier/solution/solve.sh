#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd /app

patch -p1 < "$ROOT_DIR/patches/line_validity/validity_line.rs.patch"
patch -p1 < "$ROOT_DIR/patches/walk_parent/chain_walk.rs.patch"
patch -p1 < "$ROOT_DIR/patches/budget_rss/combine.rs.patch"
patch -p1 < "$ROOT_DIR/patches/gate_operator/authorize.rs.patch"
patch -p1 < "$ROOT_DIR/patches/matrix_limits/band.rs.patch"
patch -p1 < "$ROOT_DIR/patches/row_publish/publish.rs.patch"
patch -p1 < "$ROOT_DIR/patches/src/cli_driver.rs.patch"

/usr/local/cargo/bin/cargo build --release
install -m 0755 /app/target/release/calbind /app/bin/calbind
bash /app/scripts/reset-workspace.sh
test -x /app/bin/calbind
echo "lab-instrument-calibration-chain-dossier oracle ready"
