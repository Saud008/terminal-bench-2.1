#!/usr/bin/env bash
set -euo pipefail

export RUSTUP_HOME="${RUSTUP_HOME:-/usr/local/rustup}"
export CARGO_HOME="${CARGO_HOME:-/usr/local/cargo}"
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
export CARGO_INCREMENTAL=0

cd /app
find /app/crates/combat-core/src -name '*.rs' -exec touch {} +
cargo build --offline --locked --release --bin turnctl
install -m 0755 target/release/turnctl /usr/local/bin/turnctl
