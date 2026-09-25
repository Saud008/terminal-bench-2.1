#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/src/grammar/prec.rs" /app/src/grammar/prec.rs
cp "$ROOT/src/climb/engine.rs" /app/src/climb/engine.rs
cp "$ROOT/src/climb/mod.rs" /app/src/climb/mod.rs
cp "$ROOT/src/parse/whitespace.rs" /app/src/parse/whitespace.rs
cp "$ROOT/src/parse/predicate.rs" /app/src/parse/predicate.rs
cp "$ROOT/src/parse/mod.rs" /app/src/parse/mod.rs
cp "$ROOT/src/export/span.rs" /app/src/export/span.rs
cp "$ROOT/src/export/mod.rs" /app/src/export/mod.rs

cd /app
/usr/local/cargo/bin/cargo build --release
cp /app/target/release/pestctl /app/bin/pestctl
