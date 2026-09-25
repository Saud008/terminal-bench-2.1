#!/usr/bin/env bash
set -euo pipefail
cd /app/environment
CARGO_TARGET_DIR=/app/environment/target /usr/local/cargo/bin/cargo build --release --locked
install -m 0755 target/release/shift-pl /app/bin/shift-pl
