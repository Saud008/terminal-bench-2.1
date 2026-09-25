#!/usr/bin/env bash
set -euo pipefail

PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/patches"
cp "$PATCH_DIR/tw1_canonical_lines.rs" /app/src/canonical/mod.rs
cp "$PATCH_DIR/distinct_signer_quorum.rs" /app/src/crypto/quorum.rs
cp "$PATCH_DIR/revocation_epoch_ge.rs" /app/src/crypto/revocation.rs
cp "$PATCH_DIR/witness_provenance_chain.rs" /app/src/ledger/provenance.rs
cp "$PATCH_DIR/replay_witness_merge.rs" /app/src/ledger/replay.rs
cp "$PATCH_DIR/release_witness_export.rs" /app/src/emit/mod.rs
cp "$PATCH_DIR/epoch_quorum_runner.rs" /app/src/quorum/mod.rs

cd /app
mkdir -p /app/bin /app/state /app/output
cargo build --release --locked
cp /app/target/release/twctl /app/bin/twctl
