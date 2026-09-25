#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
export CARGO_NET_OFFLINE=true

BROKEN="/opt/verifier-broken-archecore"
CORE="/app/crates/archecore/src"

cp -f "${BROKEN}/runner.rs" "${CORE}/migrate/runner/mod.rs"
cp -f "${BROKEN}/ledger.rs" "${CORE}/migrate/ledger/mod.rs"
cp -f "${BROKEN}/world.rs" "${CORE}/storage/world.rs"
cp -f "${BROKEN}/component.rs" "${CORE}/storage/component.rs"
cp -f "${BROKEN}/sparse.rs" "${CORE}/storage/sparse.rs"
cp -f "${BROKEN}/archetype.rs" "${CORE}/storage/archetype.rs"
cp -f "${BROKEN}/cache.rs" "${CORE}/query/cache.rs"
cp -f "${BROKEN}/planner.rs" "${CORE}/query/planner.rs"
cp -f "${BROKEN}/snapshot.rs" "${CORE}/staging/snapshot.rs"
cp -f "${BROKEN}/publish.rs" "${CORE}/export/publish.rs"
cp -f "${BROKEN}/wrap.rs" "${CORE}/export/wrap.rs"

cd /app
cargo build --offline --release --locked -p archectl
install -m 0755 target/release/archectl /usr/local/bin/archectl
bash /app/scripts/reset-state.sh
