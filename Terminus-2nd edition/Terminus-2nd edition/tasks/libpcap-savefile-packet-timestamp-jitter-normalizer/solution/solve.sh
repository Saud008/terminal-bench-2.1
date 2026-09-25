#!/bin/bash
set -euo pipefail

cd /app
mkdir -p /app/state /app/output

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIX="${SCRIPT_DIR}/files"
DEST="/app/crates/pcapjitter/src"

for file in parse.rs export_stage.rs ledger.rs wrap.rs; do
  cp "${FIX}/${file}" "${DEST}/${file}"
done

export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cargo build --locked -p pcapjitter

PCAP="/app/fixtures/captures/001-window-order.pcap"
/app/target/debug/pcapjitter ingest \
  --input "${PCAP}" \
  --staging /app/state/pcap-stage.json \
  --ledger-root /app/state

/app/target/debug/pcapjitter export \
  --output /app/output/timeline.json \
  --staging /app/state/pcap-stage.json \
  --ledger-root /app/state

echo "pcapjitter oracle complete"
