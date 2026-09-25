#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in checkpoint.rs manifest.rs cache.rs merge.rs; do
  cp "${DIR}/patches/${f}" "/app/crates/qwindex-core/src/${f}"
done
cd /app
cargo build --locked --release --bin qwindex
install -m 0755 target/release/qwindex /usr/local/bin/qwindex
