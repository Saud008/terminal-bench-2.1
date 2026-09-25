#!/usr/bin/env bash
set -euo pipefail
cd /app/environment
cargo build --release
install -m 0755 target/release/k7cal /app/bin/k7cal
