# Replay manifest and ledger seal

`hitreplay sample` writes two staging artifacts before export may run:

| Path | Role |
|------|------|
| `/app/state/replay-manifest.json` | Input binding and sampling metadata |
| `/app/state/tick-ledger.jsonl` | Per-tick hits and events (see `tick-ledger-schema.md`) |

`hitreplay export` must load the manifest, verify it matches the ledger header and on-disk inputs, then aggregate the ledger per `replay-export.md`.

## Manifest fields

| Field | Meaning |
|-------|---------|
| `epoch` | Monotonic sampling generation; increments on every successful `sample` |
| `entities_sha256` | Lowercase hex SHA-256 of the entities JSON bytes used for sampling |
| `animation_sha256` | Lowercase hex SHA-256 of the animation JSONL bytes used for sampling |
| `tick_rate` | Tick rate used during sampling |
| `anim_fps` | Animation FPS used during sampling |
| `max_tick` | Inclusive max tick sampled |
| `row_count` | Number of tick rows appended after the ledger header |

Export must reject stale or mismatched manifests: ledger header epoch must equal manifest epoch, row counts must match, and SHA-256 fields must match the files passed to export when paths are supplied.

Export binding validation applies to any entities and animation paths passed on the CLI, including bundled catalogs under /opt/verifier-fixtures/ (verifier harness paths TB3_ENTITIES and TB3_ANIMATION). Mismatch between manifest entity or animation SHA-256 and the files supplied to export must fail export even when the bundled alpha fixtures were used for sampling.

## Ledger header line

The first JSONL line is a header object, not a tick row:

```json
{"_kind":"header","epoch":3,"row_count":121}
```

Tick rows follow in ascending tick order. Export must not treat the header as simulation data.

## CLI split

- `hitreplay sample` — ingest entities and animation, append ledger rows, write manifest.
- `hitreplay export` — validate manifest and ledger seal, sort aggregates, write the collision report.
- `hitreplay replay` — convenience wrapper that runs sample then export with the same flags.
