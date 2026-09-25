#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/src/resolve/chain.rs" /app/src/resolve/chain.rs
cp "$ROOT/src/resolve/ref_base.rs" /app/src/resolve/ref_base.rs
cp "$ROOT/src/resolve/ofs_base.rs" /app/src/resolve/ofs_base.rs
cp "$ROOT/src/inflate/patch.rs" /app/src/inflate/patch.rs
cp "$ROOT/src/inflate/zlib.rs" /app/src/inflate/zlib.rs
cp "$ROOT/src/export/mod.rs" /app/src/export/mod.rs

cd /app
cargo build --release
cp /app/target/release/packctl /app/bin/packctl
