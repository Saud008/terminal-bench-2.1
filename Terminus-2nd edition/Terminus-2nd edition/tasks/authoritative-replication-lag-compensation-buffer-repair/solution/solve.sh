#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in lag.rs buffer.rs ledger.rs rollback.rs ingest.rs sim.rs trace_path.rs snapshot.rs export.rs; do
  cp "${DIR}/patches/${f}" "/app/crates/replic-lag-core/src/${f}"
done
cd /app
cargo build --locked --release --bin replag-sim
install -m 0755 target/release/replag-sim /usr/local/bin/replag-sim
