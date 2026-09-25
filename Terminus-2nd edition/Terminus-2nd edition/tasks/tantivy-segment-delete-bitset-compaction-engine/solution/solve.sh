#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/src/merge/bitset.rs" /app/src/merge/bitset.rs
cp "$ROOT/src/merge/freqs.rs" /app/src/merge/freqs.rs
cp "$ROOT/src/merge/stats.rs" /app/src/merge/stats.rs
cp "$ROOT/src/merge/postings.rs" /app/src/merge/postings.rs
cp "$ROOT/src/export/mod.rs" /app/src/export/mod.rs

cd /app
export PATH="/usr/local/cargo/bin:/app/bin:${PATH}"
cargo build --release
cp /app/target/release/tantictl /app/bin/tantictl
