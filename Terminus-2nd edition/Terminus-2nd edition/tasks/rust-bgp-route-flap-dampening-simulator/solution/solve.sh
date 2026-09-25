#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

rm -rf /app/target
/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/rdampctl /app/bin/rdampctl
bash /app/scripts/reset-state.sh
test -x /app/bin/rdampctl
grep -q 'half_life_ms + mid' /app/lattice/rtl_ms.rs
grep -vq 'half_life_ms / 1000' /app/lattice/rtl_ms.rs
echo "rust-bgp-route-flap-dampening-simulator oracle ready"
