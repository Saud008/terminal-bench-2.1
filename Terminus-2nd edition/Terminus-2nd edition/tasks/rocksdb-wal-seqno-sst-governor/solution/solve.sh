#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/wal/visibility.rs" /app/src/wal/visibility.rs
cp "$ROOT/compaction/planner.rs" /app/src/compaction/planner.rs
cp "$ROOT/compaction/tombstone.rs" /app/src/compaction/tombstone.rs
cp "$ROOT/merge/operator.rs" /app/src/merge/operator.rs
cp "$ROOT/witness/idempotency.rs" /app/src/witness/idempotency.rs

cd /app
cargo build --release
cp /app/target/release/rocksctl /app/bin/rocksctl
