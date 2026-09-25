#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORACLE="${SCRIPT_DIR}/oracle"
DEST="${APP_ROOT}/crates/ldif-core/src"

install -m 0644 "${ORACLE}/ldif_token_parser.rs" "${DEST}/parser.rs"
install -m 0644 "${ORACLE}/directory_semantics_apply.rs" "${DEST}/apply.rs"

cd "${APP_ROOT}"
cargo build --locked --release --bin ldif-apply
install -m 0755 target/release/ldif-apply /usr/local/bin/ldif-apply
bash "${APP_ROOT}/scripts/reset-state.sh"
