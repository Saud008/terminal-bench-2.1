#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:${PATH}"
cd /app/environment
export CARGO_TARGET_DIR=/app/environment/target
cargo build --release
install -m 0755 target/release/ctwrelease /app/bin/ctwrelease
