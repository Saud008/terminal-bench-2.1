#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_DIR="${SCRIPT_DIR}/patches"
for candidate in "${PATCH_DIR}" "/solution/patches"; do
  if [[ -f "${candidate}/golden_decode.rs" ]]; then
    PATCH_DIR="${candidate}"
    break
  fi
done

CORE="/app/crates/mav-core/src"
for mod in parse validate seed session dedup checkpoint route fact_diff snapshot publish decode; do
  cp -f "${PATCH_DIR}/golden_${mod}.rs" "${CORE}/${mod}.rs"
done

find "${CORE}" -name '*.rs' -exec sed -i 's/\r$//' {} +

cargo build --locked --release --bin mavctl
install -m 0755 /app/target/release/mavctl /usr/local/bin/mavctl
bash /app/scripts/reset-state.sh
