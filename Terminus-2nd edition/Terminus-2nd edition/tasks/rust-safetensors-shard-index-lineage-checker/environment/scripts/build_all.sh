#!/usr/bin/env bash
set -euo pipefail
cd /app/environment
CARGO_TARGET_DIR=/app/environment/target
mkdir -p /app/bin
cargo build --release
install -m 0755 target/release/xr7 /app/bin/xr7
