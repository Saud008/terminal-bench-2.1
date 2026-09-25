#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/src/canonical/mod.rs" /app/src/canonical/mod.rs
cp "$ROOT/src/crypto/expiry.rs" /app/src/crypto/expiry.rs
cp "$ROOT/src/crypto/threshold.rs" /app/src/crypto/threshold.rs
cp "$ROOT/src/delegation/paths.rs" /app/src/delegation/paths.rs
cp "$ROOT/src/delegation/reuse.rs" /app/src/delegation/reuse.rs
cp "$ROOT/src/snapshot/link.rs" /app/src/snapshot/link.rs
cp "$ROOT/src/export/mod.rs" /app/src/export/mod.rs

cd /app
cargo build --release --locked
cp /app/target/release/tufctl /app/bin/tufctl
