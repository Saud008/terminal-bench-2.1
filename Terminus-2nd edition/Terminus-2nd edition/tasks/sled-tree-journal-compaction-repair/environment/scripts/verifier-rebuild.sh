#!/usr/bin/env bash
set -euo pipefail
cd /app
cargo clean -p sledtool -p sled_engine
cargo build --locked --release --bin sledtool
install -m 0755 target/release/sledtool /usr/local/bin/sledtool
