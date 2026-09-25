Implement the three-stage agg-run pipeline under /app/bin/agg-run so JSONL event streams under a --stream-dir produce compliant staging artifacts, a ledger manifest, window rollups, and /app/output/aggregate-report.json per /app/docs/contract.md, /app/docs/staging-schema.md, /app/docs/manifest-schema.md, and /app/docs/export-schema.md.

Stage 1 (/app/lib/ingest.awk) scans *.jsonl recursively, applies first-win deduplication and numeric validation, and writes /app/state/accepted.ndjson and /app/state/ingest-stats.json (see staging-schema). Stage 2 (/app/lib/bucket.awk) reads staging only and writes /app/state/bucket-rollup.ndjson (see staging-schema). Stage 3 (/app/lib/export.awk) validates /app/state/ledger-manifest.json, reads the rollup and ingest stats, and writes the final report. The wrapper must compute the ledger manifest and maintain /app/state/run-seq.json across runs as described in /app/docs/pipeline-overview.md.

Window boundaries are UTC tumbling buckets from /app/config/window.json. Export windows sorted by ascending bucket_start, and each window series sorted by (tenant, metric) lexicographically. Footer total_events counts accepted ingest events, not window buckets. Re-running the same stream directory must produce identical report JSON and an unchanged run_seq when the input fingerprint is unchanged.

If --stream-dir is missing or not a readable directory, agg-run must exit with status 1.

/app/lib/window_legacy.awk and /app/lib/prefilter.awk are legacy helpers and are not invoked by agg-run.

Use /app/scripts/reset-state.sh before local runs. Example:

/app/scripts/reset-state.sh
/app/bin/agg-run --stream-dir /app/fixtures/streams --config /app/config/window.json --output /app/output/aggregate-report.json

Do not edit /app/docs/, /app/fixtures/streams/, /app/config/window.json, or files under /tests/.
