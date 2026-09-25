#!/usr/bin/env bash
set -euo pipefail
cd /app
ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"

require_file() {
  local candidate="$1"
  if [[ ! -f "$candidate" ]]; then
    echo "oracle missing patch file: $candidate" >&2
    exit 1
  fi
}

for patch in crypto_authdata registry_aaguid policy_uv replay_cred cache_batch trust_emit; do
  require_file "$ROOT_DIR/files/${patch}.rs"
done

install -m 0644 "$ROOT_DIR/files/crypto_authdata.rs" /app/src/ak01/wire_body.rs
install -m 0644 "$ROOT_DIR/files/registry_aaguid.rs" /app/src/ak02/vendor_map.rs
install -m 0644 "$ROOT_DIR/files/policy_uv.rs" /app/src/ak03/uv_gate.rs
install -m 0644 "$ROOT_DIR/files/replay_cred.rs" /app/src/ak04/sign_row.rs
install -m 0644 "$ROOT_DIR/files/cache_batch.rs" /app/src/ak05/row_seq.rs
install -m 0644 "$ROOT_DIR/files/trust_emit.rs" /app/src/ak06/emit.rs

for rel in ak01/wire_body.rs ak02/vendor_map.rs ak03/uv_gate.rs ak04/sign_row.rs ak05/row_seq.rs ak06/emit.rs; do
  test -f "/app/src/${rel}" || { echo "oracle install missing /app/src/${rel}" >&2; exit 1; }
done

bash /app/scripts/reset-state.sh
/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/fido2eval /app/bin/fido2eval

/app/bin/fido2eval run-batch \
  --batch batch-alpha \
  --bundle enterprise-trust \
  --policy enterprise-strict \
  --output /app/output/oracle-smoke-trust.json

test -s /app/output/oracle-smoke-trust.json
test -s /app/var/transcript-rows.json
test -s /app/var/policy-bind.json
