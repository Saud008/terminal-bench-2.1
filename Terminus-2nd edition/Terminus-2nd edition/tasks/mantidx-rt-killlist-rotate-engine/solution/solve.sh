#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
APP="${APP_ROOT:-/app}"
CORE="${APP}/crates/mantidx-core/src"

cp "${ROOT}/golden_rotate.rs" "${CORE}/rotate.rs"
cp "${ROOT}/golden_binlog.rs" "${CORE}/binlog.rs"
cp "${ROOT}/golden_killlist.rs" "${CORE}/killlist.rs"
cp "${ROOT}/golden_ram_merge.rs" "${CORE}/ram_merge.rs"
cp "${ROOT}/golden_attribute.rs" "${CORE}/attribute.rs"
cp "${ROOT}/golden_search.rs" "${CORE}/search.rs"

cd "${APP}"
cargo build --offline --locked --release --bin mantidx
install -m 0755 target/release/mantidx /usr/local/bin/mantidx
