#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app
cargo build --release --locked -p craft-cli
install -m 0755 /app/target/release/crafter /usr/local/bin/crafter
