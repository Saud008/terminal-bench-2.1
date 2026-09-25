#!/usr/bin/env bash
set -euo pipefail
cd /app
cargo build --release --locked
install -m 0755 /app/target/release/rvk9 /app/bin/rvk9
