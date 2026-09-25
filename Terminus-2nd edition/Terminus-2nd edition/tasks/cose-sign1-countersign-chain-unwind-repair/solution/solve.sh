#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_header_canon.rs" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden sources not found" >&2
  exit 1
fi

cd "${APP_ROOT}"
mkdir -p /app/output /app/state

DEST="${APP_ROOT}/crates/cose-audit/src"
cp -f "${SOL_DIR}/golden_header_canon.rs" "${DEST}/header_canon.rs"
cp -f "${SOL_DIR}/golden_sig_base.rs" "${DEST}/sig_base.rs"
cp -f "${SOL_DIR}/golden_countersign_order.rs" "${DEST}/countersign_order.rs"
cp -f "${SOL_DIR}/golden_curve_verify.rs" "${DEST}/curve_verify.rs"
cp -f "${SOL_DIR}/golden_export.rs" "${DEST}/export.rs"

cargo build --release --locked -p cose-audit
install -m 0755 target/release/cose-audit /usr/local/bin/cose-audit

bash /app/scripts/reset-state.sh

for f in /app/fixtures/cose/*.cose; do
  cose-audit ingest \
    --input "${f}" \
    --ledger /app/state/audit.db \
    --staging /app/state/cose-stage.json
done

cose-audit export \
  --ledger /app/state/audit.db \
  --staging /app/state/cose-stage.json \
  --manifest /app/output/chain-manifest.json
