# Oracle solve — task identity rust-webbundle-integrity-section-verifier wbleguard-restructure token 9d4e2b71
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

for patch in sb_url_norm sb_scope_guard sb_hdr_fold sb_ihsh_digest sb_variant_pick sb_mime_guard sb_attestation_ledger sb_attestation_emit; do
  require_file "$ROOT_DIR/files/${patch}.rs"
done

sed -i 's/u32::from_be_bytes/u32::from_le_bytes/' "$ENV/src/reader/wble_reader.rs"

install -D -m 0644 "$ROOT_DIR/files/sb_url_norm.rs" "$ENV/src/norm/url_norm.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_scope_guard.rs" "$ENV/src/policy/scope_guard.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_hdr_fold.rs" "$ENV/src/headers/hdr_fold.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_ihsh_digest.rs" "$ENV/src/integrity/ihsh_digest.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_variant_pick.rs" "$ENV/src/variants/variant_pick.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_mime_guard.rs" "$ENV/src/policy/mime_guard.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_attestation_ledger.rs" "$ENV/src/pipeline/attestation_ledger.rs"
install -D -m 0644 "$ROOT_DIR/files/sb_attestation_emit.rs" "$ENV/src/pipeline/attestation_emit.rs"

cd /app/environment
export CARGO_TARGET_DIR=/app/environment/target
rm -rf target
cargo build --release -p wbleguard
install -D -m 0755 target/release/wbleguard /app/environment/bin/wbleguard
mkdir -p /app/state /app/output
BUND="${TB3_BUNDLE_DIR:-/app/environment/fixtures/bundles}"
/app/environment/bin/wbleguard catalog-bundles --bundles-dir "$BUND" --staging /app/state/exchange_attestation.jsonl
/app/environment/bin/wbleguard emit-attestation --staging /app/state/exchange_attestation.jsonl --out /app/output/bundle_attestation_report.json
