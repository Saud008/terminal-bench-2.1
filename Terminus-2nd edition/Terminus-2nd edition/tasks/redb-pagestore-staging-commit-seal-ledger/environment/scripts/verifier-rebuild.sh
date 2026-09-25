#!/usr/bin/env bash
set -euo pipefail
cd /app
cargo clean -p redbtool
cargo build --locked --release --bin redbtool
install -m 0755 target/release/redbtool /usr/local/bin/redbtool
