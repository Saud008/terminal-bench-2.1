#!/usr/bin/env bash
set -euo pipefail
cd /app

ROOT="$(cd "$(dirname "$0")" && pwd)"
FILES="$ROOT/files"

install -m 0644 "$FILES/stg_wal/persist.rs" /app/stg_wal/persist.rs
install -m 0644 "$FILES/netpfx/envelope.rs" /app/netpfx/envelope.rs
install -m 0644 "$FILES/netpfx/canon.rs" /app/netpfx/canon.rs
install -m 0644 "$FILES/atlas_out/layout.rs" /app/atlas_out/layout.rs
install -m 0644 "$FILES/atlas_out/serialize.rs" /app/atlas_out/serialize.rs
install -m 0644 "$FILES/scope_fit/drop_ranges.rs" /app/scope_fit/drop_ranges.rs
install -m 0644 "$FILES/prov_chart/fork_log.rs" /app/prov_chart/fork_log.rs
install -m 0644 "$FILES/rank_sel/tiebreak.rs" /app/rank_sel/tiebreak.rs

/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/geocur /app/bin/geocur
bash /app/scripts/reset-state.sh
test -x /app/bin/geocur
echo "rust-geoip-prefix-overlap-routing-curator oracle ready"
