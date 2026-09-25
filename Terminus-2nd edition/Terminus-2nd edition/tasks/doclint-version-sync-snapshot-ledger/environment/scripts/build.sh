#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
export CARGO_INCREMENTAL=0
export CARGO_NET_OFFLINE=true
cd /app
cargo build --offline --release --locked -p term-lsp
install -m 0755 target/release/term-lsp /usr/local/bin/term-lsp
