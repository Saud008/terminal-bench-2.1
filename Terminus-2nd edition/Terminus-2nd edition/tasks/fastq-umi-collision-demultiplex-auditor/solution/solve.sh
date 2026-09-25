#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/src/lane/precedence.rs" /app/src/lane/precedence.rs
cp "$ROOT/src/demux/pair_sync.rs" /app/src/demux/pair_sync.rs
cp "$ROOT/src/demux/barcode.rs" /app/src/demux/barcode.rs
cp "$ROOT/src/demux/umi.rs" /app/src/demux/umi.rs
cp "$ROOT/src/collision/family.rs" /app/src/collision/family.rs
cp "$ROOT/src/export/contamination.rs" /app/src/export/contamination.rs

cd /app
/usr/local/cargo/bin/cargo build --release
cp /app/target/release/lumidmx /app/bin/lumidmx
