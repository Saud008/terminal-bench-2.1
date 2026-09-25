#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export CARGO_INCREMENTAL=0
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_read.rs" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden sources not found" >&2; exit 1; }

DEST="/app/crates/bag-audit/src"
cp -f "${SOL}/golden_read.rs" "${DEST}/bag/read.rs"
cp -f "${SOL}/golden_gap.rs" "${DEST}/bag/gap.rs"
cp -f "${SOL}/golden_deadline.rs" "${DEST}/qos/deadline.rs"
cp -f "${SOL}/golden_sqlite.rs" "${DEST}/export/sqlite.rs"

cargo build --release --locked -p bag-audit
install -m 0755 /app/target/release/bag-audit /usr/local/bin/bag-audit
echo "oracle: installed bag-audit"
