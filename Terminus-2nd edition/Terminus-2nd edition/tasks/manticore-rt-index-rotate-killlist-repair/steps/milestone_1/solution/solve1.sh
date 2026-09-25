#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/steps/milestone_1/solution"; do
  if [[ -f "${candidate}/patches/rotate.rs" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [[ -z "${SOL_DIR}" ]]; then
  echo "oracle: milestone 1 patches not found" >&2
  exit 1
fi

for f in rotate.rs binlog.rs; do
  cp "${SOL_DIR}/patches/${f}" "${APP_ROOT}/crates/mantidx-core/src/${f}"
done

cd "${APP_ROOT}"
cargo build --locked --release --bin mantidx
install -m 0755 target/release/mantidx /usr/local/bin/mantidx
test -x /usr/local/bin/mantidx
