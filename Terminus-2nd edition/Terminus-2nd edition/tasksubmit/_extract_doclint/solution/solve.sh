#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
export CARGO_INCREMENTAL=0
export CARGO_NET_OFFLINE=true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_utf16.rs" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_utf16.rs not found" >&2; exit 1; }

cp -f "${SOL}/golden_utf16.rs" "${APP_ROOT}/crates/docmodel/src/utf16.rs"
cp -f "${SOL}/golden_apply.rs" "${APP_ROOT}/crates/docmodel/src/apply.rs"
cp -f "${SOL}/golden_buffer.rs" "${APP_ROOT}/crates/docmodel/src/buffer.rs"
cp -f "${SOL}/golden_change.rs" "${APP_ROOT}/crates/docsync/src/change.rs"
cp -f "${SOL}/golden_lifecycle.rs" "${APP_ROOT}/crates/docsync/src/lifecycle.rs"
cp -f "${SOL}/golden_snapshot.rs" "${APP_ROOT}/crates/docexport/src/snapshot.rs"

cd "${APP_ROOT}"
cargo build --offline --release --locked -p term-lsp
install -m 0755 target/release/term-lsp /usr/local/bin/term-lsp
bash /app/scripts/reset-state.sh
echo "term-lsp oracle ready"
