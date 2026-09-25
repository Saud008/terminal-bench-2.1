#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export CARGO_NET_OFFLINE="${CARGO_NET_OFFLINE:-true}"

bash /app/scripts/reset-state.sh
cd /app
cargo build --offline --locked --release -p nlctl
install -m 0755 target/release/nlctl /usr/local/bin/nlctl
