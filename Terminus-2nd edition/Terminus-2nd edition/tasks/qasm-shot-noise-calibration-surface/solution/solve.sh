# Oracle solve — task identity qasm-shot-noise-calibration-surface token eb9951dd
#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/histogram/normalize.rs" /app/src/histogram/normalize.rs
cp "$ROOT/mitigate/select.rs" /app/src/mitigate/select.rs
cp "$ROOT/provenance/chain.rs" /app/src/provenance/chain.rs
cp "$ROOT/drift/readout.rs" /app/src/drift/readout.rs
cp "$ROOT/envelope/interval.rs" /app/src/envelope/interval.rs
cp "$ROOT/export/report.rs" /app/src/export/report.rs

cd /app
/usr/local/cargo/bin/cargo build --release
cp /app/target/release/qasmenv /app/bin/qasmenv
