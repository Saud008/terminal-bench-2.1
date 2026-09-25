#!/bin/bash
set -euo pipefail
ENV="/app/environment"
ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"

require_file() {
  local candidate="$1"
  if [[ ! -f "$candidate" ]]; then
    echo "oracle missing patch file: $candidate" >&2
    exit 1
  fi
}

for patch in sb_header_scan sb_stanza_fp sb_stanza_allow sb_quorum_gate sb_corpus_walk sb_decision sb_witness_stage sb_ledger_emit; do
  require_file "$ROOT_DIR/files/${patch}.rs"
done

install -D -m 0644 "$ROOT_DIR/files/sb_header_scan.rs" "$ENV/src/parse/header_scan.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_stanza_fp.rs" "$ENV/src/fingerprint/stanza_fp.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_stanza_allow.rs" "$ENV/src/policy/stanza_allow.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_quorum_gate.rs" "$ENV/src/policy/quorum_gate.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_corpus_walk.rs" "$ENV/src/admit/corpus_walk.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_decision.rs" "$ENV/src/admit/decision.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_witness_stage.rs" "$ENV/src/seal/witness_stage.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_ledger_emit.rs" "$ENV/src/seal/ledger_emit.rs"

cd /app/environment
export CARGO_TARGET_DIR=/app/environment/target
rm -rf target
cargo build --release --locked -p agerecv
install -D -m 0755 target/release/agerecv /app/environment/bin/agerecv
mkdir -p /app/state /app/output
CORPUS="${AGE_CORPUS_DIR:-/app/environment/fixtures/corpus}"
POLICY="/app/environment/fixtures/policy/pins.json"
/app/environment/bin/agerecv stage-witness --corpus "$CORPUS" --policy "$POLICY" --witness /app/state/age-header-witness.json
/app/environment/bin/agerecv seal-ledger --witness /app/state/age-header-witness.json --policy "$POLICY" --out /app/output/age-admission-ledger.json
