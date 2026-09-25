#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# patches/m1/ mirrors steps/milestone_1/solution/patches/ for Harbor /oracle mount layout
M1="${DIR}/patches/m1"
M2="${DIR}/patches"
for f in checkpoint.rs manifest.rs cache.rs merge.rs; do
  cp "${M1}/${f}" "/app/crates/qwindex-core/src/${f}"
done
for f in delete.rs split.rs search.rs merge.rs; do
  cp "${M2}/${f}" "/app/crates/qwindex-core/src/${f}"
done
cd /app
cargo build --locked --release --bin qwindex
install -m 0755 target/release/qwindex /usr/local/bin/qwindex
