#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES=""
for candidate in "${SCRIPT_DIR}/files" "/solution/files" "/oracle/solution/files"; do
  if [ -f "${candidate}/checkpoint/wal.rs" ]; then
    FILES="${candidate}"
    break
  fi
done
[[ -n "${FILES}" ]] || { echo "oracle solution files not found" >&2; exit 1; }

install -m 0644 "${FILES}/checkpoint/wal.rs" /app/src/checkpoint/wal.rs
install -m 0644 "${FILES}/checkpoint/lineage.rs" /app/src/checkpoint/lineage.rs
install -m 0644 "${FILES}/geo_fence/contain.rs" /app/src/geo_fence/contain.rs
install -m 0644 "${FILES}/coupler/grant_pick.rs" /app/src/coupler/grant_pick.rs
install -m 0644 "${FILES}/carveout/apply.rs" /app/src/carveout/apply.rs
install -m 0644 "${FILES}/tenure_gate/renewal.rs" /app/src/tenure_gate/renewal.rs
install -m 0644 "${FILES}/mhz_peer/touch.rs" /app/src/mhz_peer/touch.rs
install -m 0644 "${FILES}/rollup_emit/sort.rs" /app/src/rollup_emit/sort.rs
install -m 0644 "${FILES}/rollup_emit/emit.rs" /app/src/rollup_emit/emit.rs

# Normalize CRLF from Windows-authored solution files
for f in \
  /app/src/checkpoint/wal.rs \
  /app/src/checkpoint/lineage.rs \
  /app/src/geo_fence/contain.rs \
  /app/src/coupler/grant_pick.rs \
  /app/src/carveout/apply.rs \
  /app/src/tenure_gate/renewal.rs \
  /app/src/mhz_peer/touch.rs \
  /app/src/rollup_emit/sort.rs \
  /app/src/rollup_emit/emit.rs
do
  sed -i 's/\r$//' "$f"
done

/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/rflicat /app/bin/rflicat
bash /app/scripts/reset-state.sh
test -x /app/bin/rflicat
echo "radio-spectrum-license-coverage-catalog oracle ready"
