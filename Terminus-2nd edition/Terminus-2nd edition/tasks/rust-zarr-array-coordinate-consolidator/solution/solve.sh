# Oracle solve — task identity rust-zarr-array-coordinate-consolidator token d8a09f1c
#!/bin/bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:${PATH}"
cd "$(dirname "$0")"
patch -p1 -d /app/environment < patches/slot_math.patch
patch -p1 -d /app/environment < patches/manifest_read.patch
patch -p1 -d /app/environment < patches/ax_bind.patch
patch -p1 -d /app/environment < patches/key_ledger.patch
patch -p1 -d /app/environment < patches/fp_seal.patch
patch -p1 -d /app/environment < patches/row_stage.patch
patch -p1 -d /app/environment < patches/manifest_writer.patch
cd /app/environment
rm -rf target
cargo build --release
install -m 0755 target/release/mdcoll /app/bin/mdcoll
mkdir -p /app/state /app/output
MAN="${TB3_MANIFEST_DIR:-/app/environment/fixtures/manifests}"
AXES="${TB3_AXES_PATH:-/app/environment/fixtures/axes.json}"
/app/bin/mdcoll ingest --manifest-dir "$MAN" --axes "$AXES" --staging /app/state/array_staging.json
/app/bin/mdcoll export --staging /app/state/array_staging.json --out /app/output/consolidated_manifest.json
