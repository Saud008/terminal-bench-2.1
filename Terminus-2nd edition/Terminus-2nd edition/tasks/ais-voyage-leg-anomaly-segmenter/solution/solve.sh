#!/bin/bash
# Oracle solve — ais-voyage-leg-anomaly-segmenter
# Installs corrected Rust modules by file copy (no patch(1) dependency).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_ROOT=""
for candidate in "${SCRIPT_DIR}/files" "/solution/files" "/oracle/solution/files"; do
  if [ -f "${candidate}/oracle_track_snapshot_feed.rs" ]; then
    PATCH_ROOT="${candidate}"
    break
  fi
done
[[ -n "${PATCH_ROOT}" ]] || { echo "oracle patch files not found" >&2; exit 1; }

install_mod() {
  local src_name="$1"
  local dest_rel="$2"
  local src="${PATCH_ROOT}/${src_name}"
  local dest="/app/${dest_rel}"
  [[ -f "${src}" ]] || { echo "missing oracle patch ${src}" >&2; exit 1; }
  install -m 0644 "${src}" "${dest}"
  sed -i 's/\r$//' "${dest}" 2>/dev/null || true
}

install_mod oracle_ais_jsonl_codec.rs src/jsonl_codec/mod.rs
install_mod oracle_mmsi_coord_dedupe.rs src/mmsi_collapse/mod.rs
install_mod oracle_track_snapshot_feed.rs src/stream_feed/mod.rs
install_mod oracle_port_polygon_raycast.rs src/port_polygons/mod.rs
install_mod oracle_speed_over_ground_gate.rs src/sog_gate/mod.rs
install_mod oracle_voyage_leg_atlas_emit.rs src/atlas_emit/mod.rs
install_mod oracle_aux_k7_coord_round.rs src/aux_k7/mod.rs
install_mod oracle_aux_q2_lane_seed.rs src/aux_q2/mod.rs

mkdir -p /app/state /app/output
cd /app
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cargo build --locked -p aissegment

STREAM="/app/fixtures/streams/001-port-entry.jsonl"
/app/target/debug/aissegment feed \
  --input "${STREAM}" \
  --snapshot /app/state/track-snapshot.json \
  --ports /app/fixtures/ports.geojson

/app/target/debug/aissegment atlas \
  --output /app/output/voyage-atlas.json \
  --snapshot /app/state/track-snapshot.json \
  --ports /app/fixtures/ports.geojson

echo "aissegment oracle complete"
