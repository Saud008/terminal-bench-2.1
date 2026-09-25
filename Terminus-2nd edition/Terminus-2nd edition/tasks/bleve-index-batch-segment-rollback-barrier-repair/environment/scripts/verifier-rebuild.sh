#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app
cargo build --locked --release --bin blevectl
install -m 0755 target/release/blevectl /usr/local/bin/blevectl
