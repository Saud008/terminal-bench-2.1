#!/usr/bin/env bash
set -euo pipefail
cd /app/environment
CARGO_TARGET_DIR=/app/environment/target cargo build --release --locked
install -m 0755 target/release/whres /app/bin/whres
