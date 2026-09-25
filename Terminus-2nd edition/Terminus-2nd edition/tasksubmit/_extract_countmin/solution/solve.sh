#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

cd /app
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution/files"; do
  if [ -f "${candidate}/src/ingest/validate.rs" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "solution files not found" >&2; exit 1; }

cp -f "${SOL}/src/ingest/validate.rs" /app/src/ingest/validate.rs
cp -f "${SOL}/src/ingest/mod.rs" /app/src/ingest/mod.rs
cp -f "${SOL}/src/namespace/mod.rs" /app/src/namespace/mod.rs
cp -f "${SOL}/src/sketch/mod.rs" /app/src/sketch/mod.rs
cp -f "${SOL}/src/window/mod.rs" /app/src/window/mod.rs
cp -f "${SOL}/src/privacy/mod.rs" /app/src/privacy/mod.rs
cp -f "${SOL}/src/export/mod.rs" /app/src/export/mod.rs

for copied in \
  /app/src/ingest/validate.rs \
  /app/src/ingest/mod.rs \
  /app/src/namespace/mod.rs \
  /app/src/sketch/mod.rs \
  /app/src/window/mod.rs \
  /app/src/privacy/mod.rs \
  /app/src/export/mod.rs; do
  sed -i 's/\r$//' "${copied}"
done

cargo build --release
cp /app/target/release/cmsctl /app/bin/cmsctl
bash /app/scripts/reset-state.sh
test -x /app/bin/cmsctl
echo "countmin-sketch-epsilon-budget-rollup oracle ready"
