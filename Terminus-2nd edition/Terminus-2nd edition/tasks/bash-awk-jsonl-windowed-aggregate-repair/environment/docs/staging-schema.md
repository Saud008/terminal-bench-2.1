# Ingest staging schema

`agg-run` stage 1 is `/app/lib/ingest.awk`:

1. Scan JSONL inputs, apply dedup and value validation, write staging artifacts under `/app/state/`.
2. The wrapper writes `/app/state/ledger-manifest.json` (see `manifest-schema.md`).
3. `/app/lib/bucket.awk` reads staging only (never re-parse raw JSONL), writes `/app/state/bucket-rollup.ndjson`.
4. `/app/lib/export.awk` validates the manifest and emits `/app/output/aggregate-report.json`.

`/app/lib/window_legacy.awk` and `/app/lib/prefilter.awk` are **not** invoked by `agg-run`; do not treat them as authoritative.

## `/app/state/accepted.ndjson`

One JSON object per **accepted** event (after first-win dedup and numeric validation), in global ingest order:

```json
{"epoch": 1705315200, "tenant": "acme", "metric": "latency_ms", "value": 12.5}
```

- `epoch` — UTC unix seconds from the source line's `ts`.
- `value` — numeric value as JSON number.

## `/app/state/ingest-stats.json`

Counters produced by ingest (export stage must copy into the report `stats` block and footer sum):

```json
{
  "lines_read": 0,
  "events_accepted": 0,
  "events_deduped": 0,
  "events_skipped_invalid_value": 0,
  "footer_sum": 0.0
}
```

`footer_sum` is the sum of accepted numeric values. `total_events` in the export footer equals `events_accepted` from this file.

## `/app/state/bucket-rollup.ndjson`

One JSON object per `(bucket_start_sec, tenant, metric)` aggregate produced by stage 2:

```json
{"bucket": 1705315200, "tenant": "acme", "metric": "latency_ms", "sum": 30.0, "count": 2, "min": 10.0, "max": 20.0}
```

`bucket` is the UTC tumbling bucket start in unix seconds. Lines appear in ascending `(bucket, tenant, metric)` order.
