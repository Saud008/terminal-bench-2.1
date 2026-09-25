#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app
find /app/crates/geojson-core/src -name '*.rs' -exec touch {} +
cargo build --locked --release -p geojson-fix
install -m 0755 target/release/geojson-fix /usr/local/bin/geojson-fix
