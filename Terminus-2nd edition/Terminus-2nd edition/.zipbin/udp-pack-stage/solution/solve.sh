#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

cp /solution/patches/golden_seq.rs /app/crates/framecore/src/wire/seq.rs
cp /solution/patches/golden_parser.rs /app/crates/framecore/src/wire/parser.rs
cp /solution/patches/golden_loss_mask.rs /app/crates/framecore/src/wire/loss_mask.rs
cp /solution/patches/golden_gap.rs /app/crates/framecore/src/ledger/gap.rs
cp /solution/patches/golden_playhead.rs /app/crates/framecore/src/ledger/playhead.rs
cp /solution/patches/golden_tick.rs /app/crates/framecore/src/sim/tick.rs
cp /solution/patches/golden_staging_write.rs /app/crates/framecore/src/staging/write.rs
cp /solution/patches/golden_publish.rs /app/crates/framecore/src/export/publish.rs

cargo build --release --locked -p udpctl
install -m 0755 /app/target/release/udpctl /usr/local/bin/udpctl
