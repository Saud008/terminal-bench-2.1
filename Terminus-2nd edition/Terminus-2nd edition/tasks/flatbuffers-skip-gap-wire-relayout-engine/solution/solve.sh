#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/src/vtable/decode.rs" /app/src/vtable/decode.rs
cp "$ROOT/src/vtable/validate.rs" /app/src/vtable/validate.rs
cp "$ROOT/src/relayout/padding.rs" /app/src/relayout/padding.rs
cp "$ROOT/src/relayout/gaps.rs" /app/src/relayout/gaps.rs
cp "$ROOT/src/export/seal.rs" /app/src/export/seal.rs

cd /app
cargo build --release
cp /app/target/release/fbctl /app/bin/fbctl
