# Atlas atlas

Atlas writes /app/output/voyage-atlas.json with voyage_legs array, anomalies object, and leg_chain_digest hex sha256.
Atlas output path: /app/output/voyage-atlas.json

Anomalies fields are impossible_speed, duplicate_mmsi, burst_duplicate, and out_of_order non-negative integers matching feed and atlas processing.

leg_chain_digest is sha256 over UTF-8 bytes of comma-joined leg_id values in voyage_legs order with no spaces.

Missing snapshot file on atlas exits 1. Empty points after intake exits 2. Malformed snapshot JSON exits 2.
