#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_orient.rs" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_orient.rs not found" >&2; exit 1; }
DEST="${APP_ROOT}/crates/geojson-core/src"
cp -f "${SOL}/golden_area.rs" "${DEST}/area.rs"
cp -f "${SOL}/golden_close.rs" "${DEST}/close.rs"
cp -f "${SOL}/golden_sanitize.rs" "${DEST}/sanitize.rs"
cp -f "${SOL}/golden_orient.rs" "${DEST}/orient.rs"
cp -f "${SOL}/golden_nest.rs" "${DEST}/nest.rs"
cp -f "${SOL}/golden_multi.rs" "${DEST}/multi.rs"
cp -f "${SOL}/golden_staging.rs" "${DEST}/staging.rs"
cp -f "${SOL}/golden_export.rs" "${DEST}/export.rs"
cp -f "${SOL}/golden_repair.rs" "${DEST}/repair.rs"
cd "${APP_ROOT}"
cargo build --locked --release -p geojson-fix
install -m 0755 target/release/geojson-fix /usr/local/bin/geojson-fix
bash /app/scripts/reset-state.sh
geojson-fix repair --input /app/fixtures/geojson --output /app/output/repair-report.json
