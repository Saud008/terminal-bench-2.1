#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:${PATH}"
cd /app
cargo build --offline --release --locked -p srtctl
# Only root may refresh /usr/local/bin; agent builds leave /app/target/release/srtctl.
if [ "$(id -u)" -eq 0 ]; then
  install -o root -g root -m 0755 /app/target/release/srtctl /usr/local/bin/srtctl
fi
