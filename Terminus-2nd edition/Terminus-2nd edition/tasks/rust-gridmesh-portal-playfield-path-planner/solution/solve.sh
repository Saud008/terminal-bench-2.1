#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/files/cost.rs" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "solution/files/cost.rs not found" >&2; exit 1; }

cp -f "${SOL_DIR}/files/cost.rs" /app/crates/navmesh-core/src/cost.rs
cp -f "${SOL_DIR}/files/link.rs" /app/crates/navmesh-core/src/graph/link.rs
cp -f "${SOL_DIR}/files/validate.rs" /app/crates/navmesh-core/src/validate.rs
cp -f "${SOL_DIR}/files/fixed.rs" /app/crates/navmesh-core/src/fixed.rs
cp -f "${SOL_DIR}/files/seed.rs" /app/crates/navmesh-core/src/seed.rs
sed -i 's/\r$//' /app/crates/navmesh-core/src/cost.rs \
  /app/crates/navmesh-core/src/graph/link.rs \
  /app/crates/navmesh-core/src/validate.rs \
  /app/crates/navmesh-core/src/fixed.rs \
  /app/crates/navmesh-core/src/seed.rs

cargo build --release --locked -p navmeshctl
install -m 0755 /app/target/release/navmeshctl /usr/local/bin/navmeshctl
bash /app/scripts/reset-state.sh
