#!/usr/bin/env bash
set -euo pipefail
cd /app
export PATH="/usr/local/cargo/bin:${PATH}"
cargo build --locked -p binlim-cli
install -m 0755 target/debug/binlim /usr/local/bin/binlim
