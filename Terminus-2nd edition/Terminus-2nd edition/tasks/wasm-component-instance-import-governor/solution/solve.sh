#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/src/canonicalize/import_order.rs" /app/src/canonicalize/import_order.rs
cp "$ROOT/src/parse/type_index.rs" /app/src/parse/type_index.rs
cp "$ROOT/src/parse/export_section.rs" /app/src/parse/export_section.rs
cp "$ROOT/src/resolve/alias_closure.rs" /app/src/resolve/alias_closure.rs
cp "$ROOT/src/attest/digest.rs" /app/src/attest/digest.rs

cd /app
cargo build --release
cp /app/target/release/component-gov /app/bin/component-gov
