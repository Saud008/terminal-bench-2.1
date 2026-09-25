# Residual lattice schema

Path: /app/work/station-hulls/<campaign-id>.json

Conflict rejection removes that path for the campaign, including
/app/work/station-hulls/camp-conflict.json in verifier cases. Successful binds also write
paths such as /app/work/station-hulls/camp-gen.json, /app/work/station-hulls/camp-ms.json,
/app/work/station-hulls/camp-snap.json, and /app/work/station-hulls/camp-verts.json.

The lattice JSON is the intermediate snapshot certify-campaign reads.

Fields:
- materialize_generation: monotonically increasing unsigned integer; first bind for a campaign writes 1
- campaign_id: opaque campaign identifier from CLI
- bundle: bundle name matching fixtures
- microdegree_scale: integer scale used for quantization
- stations: lattice station records with residual_vertices, quantized_vertices, bbox corners,
  residual_area_u64, and vertex_count

Each bind for the same campaign id increments materialize_generation even when the bundle name changes.
