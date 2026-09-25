# Oracle solve — task identity rust-sbom-vex-impact-reachability-atlas token d3d9fa19
#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:${PATH}"

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd /app
test -d src/idcanon && test -d src/waiverq && test -d src/depcrawl

patch -p1 < "${ROOT_DIR}/patches/purl_canon_fixup.patch"
patch -p1 < "${ROOT_DIR}/patches/vex_status_rank.patch"
patch -p1 < "${ROOT_DIR}/patches/waiver_ttl_gate.patch"
patch -p1 < "${ROOT_DIR}/patches/runtime_bfs_reach.patch"
patch -p1 < "${ROOT_DIR}/patches/snapshot_digest_codec.patch"
patch -p1 < "${ROOT_DIR}/patches/exposure_ledger_emit.patch"

cargo build --release --locked
test -x /app/target/release/vexatlas
