# Level roster schema

Each level inventory.json contains:
- shard, lag_ms, lag_ceiling_ms, doc_floor, max_admit
- window {min_lon,min_lat,max_lon,max_lat}
- focus {lon,lat}
- focus_docs optional list
- documents array

Document rows: doc_id, kind (document|shard_marker), lon, lat, filter_pins, capture_seq.

Load-level appends TB3_PLAY_SALT to pin names, writes /app/state/level-roster.json, and
sets load_seq starting at 1, incrementing on each re-load against an existing roster.
Load-level also writes /app/state/run-meta.json with level and run identity.
