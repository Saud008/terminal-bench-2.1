Implement the three-stage agg-run pipeline under /app/bin/agg-run so JSONL event streams under a --stream-dir produce compliant staging artifacts, a ledger manifest with checksum binding, window rollups, and /app/output/aggregate-report.json per /app/docs/contract.md, /app/docs/staging-schema.md, /app/docs/manifest-schema.md, and /app/docs/export-schema.md. Cross-stage invariants require export to validate the manifest digest against accepted staging before publishing tumbling-window aggregates.

Stage 1 (/app/lib/ingest.awk) scans *.jsonl recursively, applies first-win deduplication and numeric validation, and writes /app/state/accepted.ndjson and /app/state/ingest-stats.json (see staging-schema). Stage 2 (/app/lib/bucket.awk) reads staging only and writes /app/state/bucket-rollup.ndjson (see staging-schema). Stage 3 (/app/lib/export.awk) validates /app/state/ledger-manifest.json, reads the rollup and ingest stats, and writes the final report. The wrapper must compute the ledger manifest and maintain /app/state/run-seq.json across runs as described in /app/docs/pipeline-overview.md. Stages must honor the wrapper-to-stage gawk -v variable names documented there (accepted_path, stats_path, rollup_path, manifest_path, output, window_sec, run_seq).

Window boundaries are UTC tumbling buckets from /app/config/window.json. Export windows sorted by ascending bucket_start, and each window series sorted by (tenant, metric) lexicographically. Footer total_events counts accepted ingest events, not window buckets. Re-running the same stream directory must produce identical report JSON and an unchanged run_seq when the input fingerprint is unchanged. Mutating JSONL bytes at the same path must change the fingerprint and increment run_seq.

If --stream-dir is missing or not a readable directory, agg-run must exit with status 1.

/app/lib/window_legacy.awk and /app/lib/prefilter.awk are legacy helpers and are not invoked by agg-run.

The shipped contract under /app/docs/, the public stream fixtures under /app/fixtures/streams/, and /app/config/window.json are fixed inputs for the pipeline; graded behavior is defined against those artifacts as given.
