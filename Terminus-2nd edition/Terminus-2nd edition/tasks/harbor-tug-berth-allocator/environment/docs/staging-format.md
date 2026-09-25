# Staging snapshot format

The ingest stage writes /app/state/ingest-snapshot.json as a JSON array. Each element contains arrival_utc, berth_id, departure_utc, mmsi, and voyage_id with keys sorted lexicographically within each object. Rows are sorted by berth_id, then arrival_utc, then voyage_id.

export reads the snapshot file bytes to compute staging_digest.
