# Berth allocator contract

## Pipeline stages

1. ingest reads JSONL dispatch rows, validates NMEA-derived MMSI against the row MMSI field, writes /app/state/ingest-snapshot.json, and inserts rows into SQLite.
2. export reads SQLite plus the staging snapshot and writes /app/output/berth-report.json.

Export totals must be derived from persisted assignments and the on-disk staging snapshot. Auxiliary rollup helpers must not drive published overlap minutes or staging digests.

## JSONL row fields

Each line is one JSON object:

- voyage_id: string voyage segment identifier
- mmsi: decimal MMSI integer from operations (must match NMEA parse)
- berth_id: berth code such as B-12
- arrival_utc: RFC3339 UTC timestamp
- departure_utc: RFC3339 UTC timestamp
- nmea_raw: AIS VDM payload string; MMSI is encoded as nine decimal digits starting at payload offset 8 (0-based) in the comma-separated body after the initial !AIVDM header fields

## Idempotency

Idempotency key is voyage_id + berth_id + arrival_utc concatenated with colons. Re-ingesting the same key must not insert a second row and must increment duplicate_rejected, not accepted.

## Concurrent overlap minutes

For a given berth_id, consider every unordered pair of assignments with intersecting [arrival, departure) intervals. Add the intersection length in whole minutes (floor) for each overlapping pair. Sum those minutes into concurrent_overlap_minutes for the berth. This is not the maximum single-assignment dwell.

## Staging snapshot

/app/state/ingest-snapshot.json is canonical JSON. Each array element uses lexicographically sorted object keys (arrival_utc, berth_id, departure_utc, mmsi, voyage_id). Rows are sorted by berth_id, then arrival_utc, then voyage_id. export reports staging_digest as lowercase hex SHA-256 of the exact snapshot file bytes on disk.

## Replay stats

replay_stats.accepted counts newly inserted rows per ingest run. replay_stats.duplicate_rejected counts rows rejected by idempotency. Duplicate rejections must occur inside the same database transaction as the insert attempt; counters must not advance when the insert rolls back.
