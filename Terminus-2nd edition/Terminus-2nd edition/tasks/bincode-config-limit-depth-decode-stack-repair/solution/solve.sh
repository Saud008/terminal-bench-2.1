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
  if [ -f "${candidate}/golden_limit.rs" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_limit.rs not found" >&2
  exit 1
fi

cd "${APP_ROOT}"
mkdir -p /app/output

DEST="${APP_ROOT}/crates/binlim-core/src"
cp -f "${SOL_DIR}/golden_limit.rs" "${DEST}/limit.rs"
cp -f "${SOL_DIR}/golden_varint.rs" "${DEST}/varint.rs"
cp -f "${SOL_DIR}/golden_bytes.rs" "${DEST}/bytes.rs"
cp -f "${SOL_DIR}/golden_visitor.rs" "${DEST}/visitor.rs"
cp -f "${SOL_DIR}/golden_error.rs" "${DEST}/error.rs"
cp -f "${SOL_DIR}/golden_decode.rs" "${DEST}/decode.rs"

cargo build --locked -p binlim-cli
install -m 0755 target/debug/binlim /usr/local/bin/binlim

binlim decode \
  --input /app/fixtures/bin/001-null.blim \
  --output /app/output/decode-report.json \
  --max-depth 8 \
  --max-bytes 4096
