# Trace ingest

ingest writes /app/state/ingest-manifest.json with events_total and read_head after walking a JSONL trace.

On the bundled baseline_ingest.jsonl trace, ingest must finish with read_head 5 and events_total 5.

Late frames whose frame_seq is below the current read_head are rejected; read_head must not decrease when a late frame is rejected.

snapshot_gap events increment gap_events in database meta and do not change read_head.

When TB3_TRACE_DIR is set to an absolute directory, ingest may pass only the trace filename; the path resolves under that directory.
