#!/usr/bin/env bash
set -euo pipefail
cd /app

export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
export CARGO_NET_OFFLINE="${CARGO_NET_OFFLINE:-true}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_parse.rs" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_parse.rs not found" >&2; exit 1; }

cp -f "${SOL}/golden_parse.rs" /app/crates/fc-alias-core/src/parse.rs
cp -f "${SOL}/golden_dag.rs" /app/crates/fc-alias-core/src/dag.rs
cp -f "${SOL}/golden_resolve.rs" /app/crates/fc-alias-core/src/resolve.rs
cp -f "${SOL}/golden_staging.rs" /app/crates/fc-alias-core/src/staging.rs

cargo build --release --locked -p fc-alias-check
install -m 0755 /app/target/release/fc-alias-check /usr/local/bin/fc-alias-check
bash /app/scripts/reset-state.sh
