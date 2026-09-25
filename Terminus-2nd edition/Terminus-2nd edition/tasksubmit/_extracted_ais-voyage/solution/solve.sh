#!/bin/bash
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p /app/state /app/output

patch -p0 -d /app < files/patches/oracle_jsonl_codec.diff
patch -p0 -d /app < files/patches/oracle_mmsi_coord_dedupe.diff
patch -p0 -d /app < files/patches/oracle_track_snapshot_feed.diff
patch -p0 -d /app < files/patches/oracle_port_polygon_raycast.diff
patch -p0 -d /app < files/patches/oracle_sog_gate.diff
patch -p0 -d /app < files/patches/oracle_voyage_atlas_emit.diff
patch -p0 -d /app < files/patches/oracle_aux_k7_coord_round.diff
patch -p0 -d /app < files/patches/oracle_aux_q2_lane_seed.diff

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
