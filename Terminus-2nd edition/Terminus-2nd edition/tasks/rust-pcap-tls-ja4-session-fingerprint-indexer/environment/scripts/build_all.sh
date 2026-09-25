#!/usr/bin/env bash
set -euo pipefail
cd /app/environment
CARGO_TARGET_DIR=/app/environment/target cargo build --release --locked -p ja4idx
install -m 0755 target/release/ja4idx /app/environment/tools/ja4idx/ja4idx
