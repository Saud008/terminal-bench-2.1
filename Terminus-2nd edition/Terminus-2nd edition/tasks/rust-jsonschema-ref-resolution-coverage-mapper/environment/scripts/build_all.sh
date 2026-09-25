#!/usr/bin/env bash
set -euo pipefail
cd /app/environment
export CARGO_TARGET_DIR=/app/environment/target
cargo build --release -p jscovmap
install -m 0755 target/release/jscovmap /app/environment/tools/jscovmap/jscovmap
