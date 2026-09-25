#!/usr/bin/env bash
set -euo pipefail
cd /app/environment
export CARGO_TARGET_DIR=/app/environment/target
cargo build --release -p wbleguard
install -D -m 0755 target/release/wbleguard /app/environment/bin/wbleguard
