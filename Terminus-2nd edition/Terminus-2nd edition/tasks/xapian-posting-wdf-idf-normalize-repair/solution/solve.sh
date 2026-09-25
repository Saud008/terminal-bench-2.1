#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/golden_collector.rs" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_collector.rs not found" >&2; exit 1; }

cp -f "${SOL_DIR}/golden_collector.rs" /app/crates/xapi-wdf/src/collector.rs
cp -f "${SOL_DIR}/golden_cf_table.rs" /app/crates/xapi-index/src/cf_table.rs
cp -f "${SOL_DIR}/golden_norm.rs" /app/crates/xapi-length/src/norm.rs
cp -f "${SOL_DIR}/golden_expand.rs" /app/crates/xapi-synonym/src/expand.rs
cp -f "${SOL_DIR}/golden_or_branch.rs" /app/crates/query-planner/src/or_branch.rs
cp -f "${SOL_DIR}/golden_store.rs" /app/crates/ingest-stage/src/store.rs
sed -i 's/\r$//' /app/crates/xapi-wdf/src/collector.rs \
  /app/crates/xapi-index/src/cf_table.rs \
  /app/crates/xapi-length/src/norm.rs \
  /app/crates/xapi-synonym/src/expand.rs \
  /app/crates/query-planner/src/or_branch.rs \
  /app/crates/ingest-stage/src/store.rs

cargo build --release --locked -p xapian-weight-cli
install -m 0755 /app/target/release/xapian-weight-cli /usr/local/bin/xapian-weight-cli
bash /app/scripts/reset-state.sh
