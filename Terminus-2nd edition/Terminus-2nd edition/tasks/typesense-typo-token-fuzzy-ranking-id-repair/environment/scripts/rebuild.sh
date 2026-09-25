#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app
cargo build --release --locked -p typesense-search-cli
install -m 0755 /app/target/release/typesense-search-cli /usr/local/bin/typesense-search-cli
