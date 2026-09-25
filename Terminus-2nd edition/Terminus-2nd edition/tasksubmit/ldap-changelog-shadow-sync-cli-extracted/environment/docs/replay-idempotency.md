# Replay idempotency

## Ingest

`/app/state/last-ingest-stats.json`:

```json
{ "new_usns": 3, "replay_noop": 0 }
```

When ingesting a changelog:

- Each `uSNChanged` value is applied at most once across the database lifetime.
- Re-submitting records whose `uSNChanged` was already applied increments `replay_noop` and must not mutate shadow or append staging lines.
- Fresh USNs increment `new_usns` and apply normally.

## Export sequence

`export_sequence` in `shadow-audit.json` advances by 1 only when the preceding ingest recorded `new_usns > 0`. Replaying only known USNs (`new_usns == 0`) must leave `export_sequence` unchanged.

`replay_stats` in the audit file must match `last-ingest-stats.json` from the ingest immediately before export.
