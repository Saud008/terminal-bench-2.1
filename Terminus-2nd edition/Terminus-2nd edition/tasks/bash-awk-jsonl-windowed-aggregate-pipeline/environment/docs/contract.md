# agg-run contract

`agg-run` ingests JSONL event streams and emits UTC tumbling-window aggregates.
See `staging-schema.md`, `manifest-schema.md`, `export-schema.md`, and
`pipeline-overview.md` for the artifact formats referenced below.

## Source event lines

Each stream file under `--stream-dir` holds one JSON object per line:

```json
{"event_id": "e1", "tenant": "acme", "metric": "latency_ms", "ts": "2024-01-15T08:00:00Z", "value": 12.5}
```

- `event_id` — dedup key (string).
- `tenant`, `metric` — series identity (strings).
- `ts` — RFC3339 UTC timestamp ending in `Z`.
- `value` — measurement. May be a JSON number or a numeric string.

## Ingest rules (stage 1)

For every non-empty line, in global discovery order (`*.jsonl` files sorted
lexicographically, lines in file order):

1. Increment `lines_read`.
2. If `event_id`, `tenant`, `metric`, or `ts` is missing/empty, increment
   `events_skipped_invalid_value` and drop the line.
3. If `event_id` was already accepted or already seen, increment
   `events_deduped` and drop the line (**first-win** dedup — the first line for
   an `event_id` wins, later lines with the same id are dropped even if the
   first line later fails value validation).
4. Otherwise mark the `event_id` as seen.
5. If `value` is not a valid number (missing, `null`, `NaN`, empty string, or a
   non-numeric string), increment `events_skipped_invalid_value` and drop the
   line. Invalid values are **skipped**, never coerced to `0`.
6. Otherwise accept the line: increment `events_accepted`, add `value` to
   `footer_sum`, and append an accepted row to `/app/state/accepted.ndjson`.

`ts` converts to `epoch` as UTC unix seconds. All gawk stages run under
`TZ=UTC`.

## Windowing (stage 2)

The UTC tumbling bucket start for an event is
`floor(epoch / window_sec) * window_sec`. Events sharing a
`(bucket, tenant, metric)` key aggregate into `sum`, `count`, `min`, `max`.
`tenant` and `metric` are distinct key components and must never be
concatenated without a separator.

## Report (stage 3)

Export validates `/app/state/ledger-manifest.json` before publishing. Windows
are sorted by ascending `bucket_start`; each window's `series` is sorted by
`(tenant, metric)` ascending. The footer `total_events` equals
`events_accepted` (accepted events, not the number of window buckets), and
`run_seq` mirrors `/app/state/run-seq.json`.
