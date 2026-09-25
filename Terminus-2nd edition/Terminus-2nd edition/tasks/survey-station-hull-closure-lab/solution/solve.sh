# Oracle solve — task identity survey-station-hull-closure-lab token ac9b3b41
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd /app

patch -p1 -i "$ROOT_DIR/geohull_rewire_steps/geoid_shift/vector.rs.diff"
patch -p1 -i "$ROOT_DIR/geohull_rewire_steps/micro_quant/scale.rs.diff"
patch -p1 -i "$ROOT_DIR/geohull_rewire_steps/antimeridian_cut/segment.rs.diff"
patch -p1 -i "$ROOT_DIR/geohull_rewire_steps/overlap_veto/pair.rs.diff"
patch -p1 -i "$ROOT_DIR/geohull_rewire_steps/geohull_rows/row_order.rs.diff"
patch -p1 -i "$ROOT_DIR/geohull_rewire_steps/seal_digest/hexline.rs.diff"

/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/stationclos /app/bin/stationclos
bash /app/scripts/reset-workspace.sh
test -x /app/bin/stationclos
echo "survey-station-hull-closure-lab oracle ready"
