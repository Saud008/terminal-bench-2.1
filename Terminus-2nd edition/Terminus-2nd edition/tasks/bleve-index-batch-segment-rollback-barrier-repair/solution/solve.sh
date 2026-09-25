#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
APP_ROOT="${APP_ROOT:-/app}"
SOLUTION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install -m 0644 "${SOLUTION_DIR}/files/writer.rs" "${APP_ROOT}/src/batch/writer.rs"
install -m 0644 "${SOLUTION_DIR}/files/store.rs" "${APP_ROOT}/src/segment/store.rs"
install -m 0644 "${SOLUTION_DIR}/files/checksum.rs" "${APP_ROOT}/src/segment/checksum.rs"
install -m 0644 "${SOLUTION_DIR}/files/scheduler.rs" "${APP_ROOT}/src/merge/scheduler.rs"
install -m 0644 "${SOLUTION_DIR}/files/allocator.rs" "${APP_ROOT}/src/id/allocator.rs"
install -m 0644 "${SOLUTION_DIR}/files/key_order.rs" "${APP_ROOT}/src/collator/key_order.rs"
install -m 0644 "${SOLUTION_DIR}/files/export_stage.rs" "${APP_ROOT}/src/export/stage.rs"

cd "${APP_ROOT}"
cargo build --locked --release --bin blevectl
install -m 0755 target/release/blevectl /usr/local/bin/blevectl
bash /app/scripts/reset-state.sh
test -x /usr/local/bin/blevectl
