#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENG="/app/crates/sled_engine/src"

cp "${SOL}/files/golden_replay.rs" "${ENG}/ingest/replay.rs"
cp "${SOL}/files/golden_split.rs" "${ENG}/btree/split.rs"
cp "${SOL}/files/golden_merge.rs" "${ENG}/btree/merge.rs"
cp "${SOL}/files/golden_underflow.rs" "${ENG}/btree/underflow.rs"
cp "${SOL}/files/golden_barrier.rs" "${ENG}/commit/barrier.rs"
cp "${SOL}/files/golden_split_log.rs" "${ENG}/journal/split_log.rs"
cp "${SOL}/files/golden_crash_replay.rs" "${ENG}/journal/crash_replay.rs"
cp "${SOL}/files/golden_reclaim.rs" "${ENG}/compaction/reclaim.rs"
cp "${SOL}/files/golden_checksum.rs" "${ENG}/page/checksum.rs"
cp "${SOL}/files/golden_range.rs" "${ENG}/export/range.rs"

bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh
