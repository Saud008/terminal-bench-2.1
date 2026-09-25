#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/golden_cost.rs" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_cost.rs not found" >&2; exit 1; }

cp -f "${SOL_DIR}/golden_cost.rs" /app/crates/navmesh-core/src/cost.rs
cp -f "${SOL_DIR}/golden_link.rs" /app/crates/navmesh-core/src/graph/link.rs
cp -f "${SOL_DIR}/golden_validate.rs" /app/crates/navmesh-core/src/validate.rs
sed -i 's/\r$//' /app/crates/navmesh-core/src/cost.rs \
  /app/crates/navmesh-core/src/graph/link.rs \
  /app/crates/navmesh-core/src/validate.rs

cargo build --release --locked -p navmeshctl
install -m 0755 /app/target/release/navmeshctl /usr/local/bin/navmeshctl
bash /app/scripts/reset-state.sh
