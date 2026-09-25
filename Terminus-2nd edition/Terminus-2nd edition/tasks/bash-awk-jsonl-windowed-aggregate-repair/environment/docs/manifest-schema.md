# Ledger manifest schema

After stage 1 completes, `agg-run` writes `/app/state/ledger-manifest.json` before stage 2 runs:

```json
{
  "manifest_version": 1,
  "accepted_sha256": "hex lowercase sha256 of accepted.ndjson raw bytes",
  "events_accepted": 42
}
```

`events_accepted` must equal `ingest-stats.json` `events_accepted` and the number of non-empty lines in `accepted.ndjson`.

Stage 3 (`export.awk`) must refuse to emit a report when the manifest is missing, when `events_accepted` disagrees with ingest stats, or when `accepted_sha256` does not match the on-disk `accepted.ndjson` digest.

The manifest binds ingest output to export so partial rollup fixes cannot publish a report against a stale ledger.
