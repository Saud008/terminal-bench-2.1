# Track snapshot schema

Feed writes JSON to /app/state/track-snapshot.json with source (resolved input path string), points array, and feed_stats object.
snapshot output path: /app/state/track-snapshot.json

Each point contains seq, mmsi, ts_epoch, lat, lon, sog, draught, station. Points must be sorted by mmsi ascending, ts_epoch ascending, seq ascending.

feed_stats includes raw_rows, after_mmsi_dedupe, after_burst counts, and out_of_order count of rows whose position changes when applying stable sort before snapshot write.
