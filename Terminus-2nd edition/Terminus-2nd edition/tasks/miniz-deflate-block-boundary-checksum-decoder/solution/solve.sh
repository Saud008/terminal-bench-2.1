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
  if [ -f "${candidate}/files/golden_adler.rs" ]; then
    SOL_DIR="${candidate}/files"
    break
  fi
  if [ -f "${candidate}/golden_adler.rs" ]; then
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

DEST="${APP_ROOT}/crates/minizdecode/src"
cp -f "${SOL_DIR}/golden_adler.rs" "${DEST}/adler.rs"
cp -f "${SOL_DIR}/golden_block_stored.rs" "${DEST}/block_stored.rs"
cp -f "${SOL_DIR}/golden_huffman_dynamic.rs" "${DEST}/huffman_dynamic.rs"
cp -f "${SOL_DIR}/golden_window.rs" "${DEST}/window.rs"
cp -f "${SOL_DIR}/golden_stream.rs" "${DEST}/stream.rs"
cp -f "${SOL_DIR}/golden_export.rs" "${DEST}/export.rs"

cargo build --locked -p minizdecode
install -m 0755 target/debug/minizdecode /usr/local/bin/minizdecode

for f in /app/fixtures/streams/*.zlib; do
  base="$(basename "${f}" .zlib)"
  minizdecode decompress \
    --input "${f}" \
    --output "/app/output/${base}.bin" \
    --report "/app/output/decompress-report.json" \
    --staging "/app/state/decode-stage.json"
done