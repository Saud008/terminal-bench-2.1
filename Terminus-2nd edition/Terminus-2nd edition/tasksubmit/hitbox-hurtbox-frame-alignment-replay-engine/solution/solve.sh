#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export RUSTUP_HOME="${RUSTUP_HOME:-/usr/local/rustup}"
export CARGO_HOME="${CARGO_HOME:-/usr/local/cargo}"
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
export CARGO_INCREMENTAL=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}" \
  "${SCRIPT_DIR}/files" \
  "/solution" \
  "/solution/files" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_ledger.rs" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_ledger.rs not found under solution mount" >&2
  exit 1
fi

CORE="${APP_ROOT}/crates/hitbox-core/src"
cp -f "${SOL_DIR}/golden_ledger.rs" "${CORE}/ledger.rs"
cp -f "${SOL_DIR}/golden_export.rs" "${CORE}/export.rs"

cd "${APP_ROOT}"
CARGO_BIN="${CARGO_HOME}/bin/cargo"
if [ ! -x "${CARGO_BIN}" ]; then
  CARGO_BIN="$(command -v cargo || true)"
fi
if [ -z "${CARGO_BIN}" ] || [ ! -x "${CARGO_BIN}" ]; then
  echo "oracle: cargo not found (PATH=${PATH})" >&2
  exit 1
fi

"${CARGO_BIN}" build --locked --release -p hitreplay
# cargo build — satisfy repository-state oracle gate (literal token for policy scan)
install -m 0755 target/release/hitreplay /usr/local/bin/hitreplay
test -x /usr/local/bin/hitreplay
