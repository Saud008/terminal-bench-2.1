# Pipeline overview

`agg-run` is a three-stage pipeline:

1. `/app/lib/ingest.awk` scans `*.jsonl` under `--stream-dir`, applies dedup and validation, writes `/app/state/accepted.ndjson` and `/app/state/ingest-stats.json` (see `staging-schema.md`).
2. The wrapper computes `/app/state/ledger-manifest.json` from accepted staging (see `manifest-schema.md`).
3. `/app/lib/bucket.awk` reads accepted staging only, buckets in UTC, writes `/app/state/bucket-rollup.ndjson`.
4. `/app/lib/export.awk` validates the manifest, reads rollup lines and ingest stats, writes `/app/output/aggregate-report.json` and updates `/app/state/run-seq.json`.

The wrapper loads `window_sec` from `/app/config/window.json`, exports `TZ=UTC` for all gawk stages, and computes an input fingerprint from sorted stream file paths and contents.

## Run sequence persistence

`/app/state/run-seq.json`:

```json
{"seq": 1, "input_fingerprint": "hex sha256"}
```

When the input fingerprint matches the stored value, `seq` stays unchanged on success. When the fingerprint changes, `seq` increments by one. The export footer `run_seq` field mirrors the stored `seq` after a successful run.

Each run replaces prior staging, rollup, manifest, and report files except `run-seq.json`, which persists until reset.

Legacy modules `/app/lib/window_legacy.awk` and `/app/lib/prefilter.awk` are not invoked.
