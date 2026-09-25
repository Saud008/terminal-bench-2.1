#!/usr/bin/env bash
set -euo pipefail
cd /app/environment
cargo build --release
install -m 0755 target/release/imgctl /app/bin/imgctl
