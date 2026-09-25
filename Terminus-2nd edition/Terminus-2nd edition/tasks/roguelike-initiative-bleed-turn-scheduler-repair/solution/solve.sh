#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export RUSTUP_HOME="${RUSTUP_HOME:-/usr/local/rustup}"
export CARGO_HOME="${CARGO_HOME:-/usr/local/cargo}"
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
export CARGO_INCREMENTAL=0
export CARGO_NET_OFFLINE=true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}/files" \
  "${SCRIPT_DIR}" \
  "/solution/files" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_ingest.rs" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_ingest.rs not found under solution mount" >&2
  exit 1
fi

DEST="${APP_ROOT}/crates/combat-core/src"
cp -f "${SOL_DIR}/golden_ingest.rs" "${DEST}/ingest.rs"
cp -f "${SOL_DIR}/golden_scheduler.rs" "${DEST}/scheduler.rs"
cp -f "${SOL_DIR}/golden_bleed.rs" "${DEST}/bleed.rs"
cp -f "${SOL_DIR}/golden_export.rs" "${DEST}/export.rs"
cp -f "${SOL_DIR}/golden_simulate.rs" "${DEST}/simulate.rs"

cd "${APP_ROOT}"
CARGO_BIN="${CARGO_HOME}/bin/cargo"
if [ ! -x "${CARGO_BIN}" ]; then
  CARGO_BIN="$(command -v cargo || true)"
fi
if [ -z "${CARGO_BIN}" ] || [ ! -x "${CARGO_BIN}" ]; then
  echo "oracle: cargo not found (PATH=${PATH})" >&2
  exit 1
fi

"${CARGO_BIN}" build --offline --locked --release --bin turnctl
install -m 0755 target/release/turnctl /usr/local/bin/turnctl
test -x /usr/local/bin/turnctl
