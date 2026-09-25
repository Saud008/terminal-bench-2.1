#!/usr/bin/env bash
# Oracle solve - wildfire-evacuation-zone-alert-bundler
set -euo pipefail

cd /app/environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_ROOT=""
for candidate in "${SCRIPT_DIR}/files" "/solution/files" "/oracle/solution/files"; do
  if [ -f "${candidate}/m01_geom.rs" ]; then
    PATCH_ROOT="${candidate}"
    break
  fi
done
[[ -n "${PATCH_ROOT}" ]] || { echo "oracle patch files not found" >&2; exit 1; }

install_patch() {
  local name="$1"
  local src="${PATCH_ROOT}/${name}"
  local dest="src/${name}"
  [[ -f "${src}" ]] || { echo "missing oracle patch ${src}" >&2; exit 1; }
  install -m 0644 "${src}" "${dest}"
  sed -i 's/\r$//' "${dest}" 2>/dev/null || true
}

install_patch m01_geom.rs
install_patch m03_slot.rs
install_patch m04_journal.rs
install_patch m05_prec.rs
install_patch m06_mesh.rs
install_patch m07_emit.rs

cargo build --release
install -m 0755 target/release/k7cal /app/bin/k7cal
/app/bin/k7cal bind --scenario dual-zone-spread --run-id smoke
/app/bin/k7cal weave --run-id smoke
/app/bin/k7cal seal --run-id smoke --output /app/output/smoke.json
echo "k7cal oracle ready"
