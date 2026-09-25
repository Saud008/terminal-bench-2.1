# Residual closure atlas

certify-campaign writes JSON to the caller-provided --output path. Verifier cases use paths under
/app/output/ such as /app/output/{campaign}.json, /app/output/iso.json, /app/output/dl.json,
and /app/output/ms.json.

rows sorted by residual_area_u64 ascending, then station_id ascending lexicographically.
rank is 1-based in that order.

Each row includes station_id, residual_area_u64, vertex_count, rank.

summary includes total_stations, wrap_parts (station_id ending in -W or -E), max_area, min_area.

closure_digest is the lowercase hex SHA-256 of newline-joined lines
`{station_id}|{residual_area_u64}|{vertex_count}` in the ranked row order (do not re-sort
digest lines independently of rank).
