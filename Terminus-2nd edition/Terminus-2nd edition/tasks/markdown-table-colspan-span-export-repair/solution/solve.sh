#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

CORE="/app/crates/mdtable-core/src"
SOL="/solution"

cp "${SOL}/golden_cells.rs" "${CORE}/parse/cells.rs"
cp "${SOL}/golden_table.rs" "${CORE}/parse/table.rs"
cp "${SOL}/golden_markers.rs" "${CORE}/span/markers.rs"
cp "${SOL}/golden_grid.rs" "${CORE}/span/grid.rs"
cp "${SOL}/golden_json.rs" "${CORE}/export/json.rs"
cp "${SOL}/golden_html.rs" "${CORE}/export/html.rs"
cp "${SOL}/golden_snapshot.rs" "${CORE}/snapshot/mod.rs"
cp "${SOL}/golden_publish.rs" "${CORE}/export/publish.rs"

cargo build --release --locked --offline -p mdtable
install -m 0755 /app/target/release/mdtable /usr/local/bin/mdtable
bash /app/scripts/reset-state.sh
