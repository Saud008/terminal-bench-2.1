#!/bin/bash
# Oracle CT witness auditor — token f3c91e7a2b
set -euo pipefail
export PATH="/usr/local/cargo/bin:${PATH}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORACLE_FIXED="${ROOT}/fixed"
install -D -m 0644 "${ORACLE_FIXED}/src/ctpath/leaf_body.rs" "/app/environment/src/ctpath/leaf_body.rs"
install -D -m 0644 "${ORACLE_FIXED}/src/cosign/vote_tally.rs" "/app/environment/src/cosign/vote_tally.rs"
install -D -m 0644 "${ORACLE_FIXED}/src/cosign/chron_order.rs" "/app/environment/src/cosign/chron_order.rs"
install -D -m 0644 "${ORACLE_FIXED}/src/ledgerfmt/hex_norm.rs" "/app/environment/src/ledgerfmt/hex_norm.rs"
install -D -m 0644 "${ORACLE_FIXED}/src/exportkit/snapshot_lines.rs" "/app/environment/src/exportkit/snapshot_lines.rs"
install -D -m 0644 "${ORACLE_FIXED}/src/exportkit/capsule_emit.rs" "/app/environment/src/exportkit/capsule_emit.rs"
cd "${ROOT}"
patch -p0 --forward -d /app/environment < patches/ct_leaf_body.patch || true
patch -p0 --forward -d /app/environment < patches/ct_cosign_tally.patch || true
patch -p0 --forward -d /app/environment < patches/ct_chron_order.patch || true
patch -p0 --forward -d /app/environment < patches/ct_hex_norm.patch || true
patch -p0 --forward -d /app/environment < patches/ct_snapshot_lines.patch || true
patch -p0 --forward -d /app/environment < patches/ct_capsule_emit.patch || true
cd /app/environment
rm -rf target
cargo build --release --locked
install -m 0755 target/release/ctwrelease /app/bin/ctwrelease
mkdir -p /app/state /app/output
IDX="${TB3_AUDIT_INDEX:-/app/environment/fixtures/audit_index.json}"
LEDGER="${TB3_WITNESS_LEDGER:-/app/environment/fixtures/witness_ledger.json}"
/app/bin/ctwrelease stage --audit-index "$IDX" --witness-ledger "$LEDGER" --staging /app/state/checkpoint_rows.json
/app/bin/ctwrelease seal --staging /app/state/checkpoint_rows.json --out /app/output/witness_evidence_archive.json
