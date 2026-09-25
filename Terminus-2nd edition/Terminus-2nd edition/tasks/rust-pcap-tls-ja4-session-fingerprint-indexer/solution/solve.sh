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

verify_capsule_fixture() {
  local capsule_root="$1"
  if [[ ! -d "$capsule_root" ]]; then
    echo "capsule fixture directory missing: $capsule_root" >&2
    exit 1
  fi
  local cap_count
  cap_count="$(find "$capsule_root" -maxdepth 1 -type f -name '*.cap' | wc -l | tr -d ' ')"
  if [[ "$cap_count" -lt 1 ]]; then
    echo "expected at least one .cap file under $capsule_root" >&2
    exit 1
  fi
}

ensure_state_dirs() {
  mkdir -p /app/state /app/output
  rm -f /app/state/session_ledger.jsonl /app/output/session_index.json
}

verify_capsule_fixture "${TB3_CAPSULE_DIR:-/app/environment/fixtures/capsules}"
ensure_state_dirs

require_file "$ROOT_DIR/files/ja4_anomaly_tally.rs"
require_file "$ROOT_DIR/files/ja4_capsule_reader.rs"
require_file "$ROOT_DIR/files/ja4_session_report.rs"
require_file "$ROOT_DIR/files/ja4_fingerprint_canon.rs"
require_file "$ROOT_DIR/files/ja4_payload_dedupe.rs"
require_file "$ROOT_DIR/files/ja4_endpoint_roles.rs"
require_file "$ROOT_DIR/files/ja4_session_ledger.rs"
require_file "$ROOT_DIR/files/ja4_record_splice.rs"

install -D -m 0644 "$ROOT_DIR/files/ja4_anomaly_tally.rs" "$ENV/tls_lab/anomaly_count/src/anomaly_tally.rs"
install -D -m 0644 "$ROOT_DIR/files/ja4_capsule_reader.rs" "$ENV/tls_lab/capsule_io/src/reader.rs"
install -D -m 0644 "$ROOT_DIR/files/ja4_session_report.rs" "$ENV/tls_lab/index_emit/src/session_report.rs"
install -D -m 0644 "$ROOT_DIR/files/ja4_fingerprint_canon.rs" "$ENV/tls_lab/ja4_canon/src/fingerprint_canon.rs"
install -D -m 0644 "$ROOT_DIR/files/ja4_payload_dedupe.rs" "$ENV/tls_lab/retrans_dedupe/src/payload_dedupe.rs"
install -D -m 0644 "$ROOT_DIR/files/ja4_endpoint_roles.rs" "$ENV/tls_lab/role_detect/src/endpoint_roles.rs"
install -D -m 0644 "$ROOT_DIR/files/ja4_session_ledger.rs" "$ENV/tls_lab/ledger_store/src/session_ledger.rs"
install -D -m 0644 "$ROOT_DIR/files/ja4_record_splice.rs" "$ENV/tls_lab/tls_reasm/src/record_splice.rs"

cd /app/environment
rm -rf target
CARGO_TARGET_DIR=/app/environment/target cargo build --release --locked -p ja4idx
install -m 0755 target/release/ja4idx /app/environment/tools/ja4idx/ja4idx

CAPS="${TB3_CAPSULE_DIR:-/app/environment/fixtures/capsules}"
LEDGER_PATH="/app/state/session_ledger.jsonl"
INDEX="/app/output/session_index.json"
/app/environment/tools/ja4idx/ja4idx intake --capsules-dir "$CAPS" --ledger "$LEDGER_PATH"
/app/environment/tools/ja4idx/ja4idx emit --ledger "$LEDGER_PATH" --out "$INDEX"
if [[ ! -s "$LEDGER_PATH" ]]; then
  echo "ledger file empty after intake" >&2
  exit 1
fi
if [[ ! -s "$INDEX" ]]; then
  echo "session index empty after emit" >&2
  exit 1
fi
