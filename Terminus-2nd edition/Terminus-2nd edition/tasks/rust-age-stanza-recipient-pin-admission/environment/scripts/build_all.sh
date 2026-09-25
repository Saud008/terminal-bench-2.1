#!/bin/bash
set -euo pipefail
cd /app/environment
export CARGO_TARGET_DIR=/app/environment/target
cargo build --release --locked -p agerecv
install -D -m 0755 target/release/agerecv /app/environment/bin/agerecv
