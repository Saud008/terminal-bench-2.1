#!/usr/bin/env bash
set -euo pipefail
cd /app
cargo clean -p tantool
cargo build --locked --release --bin tantool
install -m 0755 target/release/tantool /usr/local/bin/tantool
