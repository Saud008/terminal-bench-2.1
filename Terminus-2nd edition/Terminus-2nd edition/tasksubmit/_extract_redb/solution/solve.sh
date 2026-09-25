#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "${SOL}/golden_split.rs" /app/src/btree/split.rs
cp "${SOL}/golden_merge.rs" /app/src/btree/merge.rs
cp "${SOL}/golden_underflow.rs" /app/src/btree/underflow.rs
cp "${SOL}/golden_barrier.rs" /app/src/commit/barrier.rs
cp "${SOL}/golden_scan.rs" /app/src/export/scan.rs
cp "${SOL}/golden_replay.rs" /app/src/ingest/replay.rs

bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh
