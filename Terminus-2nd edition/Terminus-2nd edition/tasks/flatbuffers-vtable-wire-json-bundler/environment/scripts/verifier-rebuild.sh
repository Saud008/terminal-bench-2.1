#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app
find /app/src -name '*.rs' -exec touch {} +
cargo build --locked --release -p fbpkg
install -m 0755 target/release/fbdecode /usr/local/bin/fbdecode
