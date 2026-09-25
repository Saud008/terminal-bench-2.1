#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/golden_crafter.rs" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_crafter.rs not found" >&2; exit 1; }

cp -f "${SOL_DIR}/golden_substitute.rs" /app/crates/craft-core/src/substitute.rs
cp -f "${SOL_DIR}/golden_stack.rs" /app/crates/craft-core/src/stack.rs
cp -f "${SOL_DIR}/golden_cycle.rs" /app/crates/craft-core/src/cycle.rs
cp -f "${SOL_DIR}/golden_crafter.rs" /app/crates/craft-core/src/crafter.rs
cp -f "${SOL_DIR}/golden_dao.rs" /app/crates/inventory-db/src/dao.rs
sed -i 's/\r$//' /app/crates/craft-core/src/substitute.rs \
  /app/crates/craft-core/src/stack.rs \
  /app/crates/craft-core/src/cycle.rs \
  /app/crates/craft-core/src/crafter.rs \
  /app/crates/inventory-db/src/dao.rs

cargo build --release --locked -p craft-cli
install -m 0755 /app/target/release/crafter /usr/local/bin/crafter
bash /app/scripts/reset-state.sh
