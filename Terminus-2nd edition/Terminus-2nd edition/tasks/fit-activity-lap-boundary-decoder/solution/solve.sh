#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_crc.rs" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden files not found" >&2; exit 1; }

DEST="${APP_ROOT}/crates/fitcore/src"
cp -f "${SOL}/golden_crc.rs" "${DEST}/crc.rs"
cp -f "${SOL}/golden_boundary.rs" "${DEST}/boundary.rs"
cp -f "${SOL}/golden_trigger.rs" "${DEST}/trigger.rs"
cp -f "${SOL}/golden_digest.rs" "${DEST}/digest.rs"
cp -f "${SOL}/golden_lap_time.rs" "${DEST}/lap_time.rs"
cp -f "${SOL}/golden_staging.rs" "${DEST}/staging.rs"
cp -f "${SOL}/golden_export.rs" "${DEST}/export.rs"

cd "${APP_ROOT}"
cargo build --release --locked -p fitlap
install -m 0755 /app/target/release/fitlap /usr/local/bin/fitlap
bash /app/scripts/reset-state.sh
