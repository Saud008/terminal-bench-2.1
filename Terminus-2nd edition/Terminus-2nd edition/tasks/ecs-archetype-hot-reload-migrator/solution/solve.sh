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
  "${SCRIPT_DIR}/files" \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution"; do
  if [ -f "${candidate}/golden_migrator.rs" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_migrator.rs not found under solution mount" >&2
  exit 1
fi

CORE="${APP_ROOT}/crates/ecs-core/src"
cp -f "${SOL_DIR}/golden_migrator.rs" "${CORE}/migrator.rs"
cp -f "${SOL_DIR}/golden_archetype.rs" "${CORE}/archetype.rs"
cp -f "${SOL_DIR}/golden_entity_id.rs" "${CORE}/entity_id.rs"
cp -f "${SOL_DIR}/golden_journal.rs" "${CORE}/journal.rs"
cp -f "${SOL_DIR}/golden_checksum.rs" "${CORE}/checksum.rs"
cp -f "${SOL_DIR}/golden_store.rs" "${CORE}/store.rs"

cd "${APP_ROOT}"
cargo build --locked -p ecs-migrate
install -m 0755 target/debug/ecs-migrate /usr/local/bin/ecs-migrate
test -x /usr/local/bin/ecs-migrate
