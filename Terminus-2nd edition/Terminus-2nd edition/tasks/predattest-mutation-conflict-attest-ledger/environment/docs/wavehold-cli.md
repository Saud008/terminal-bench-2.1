# wavehold CLI

`wavehold` previews a mutation-wave rollout in three stages backed by on-disk
run state. A run is keyed by `--run-id`.

## Stages

```
wavehold scan    --wave <path.jsonl> --run-id <id> [--config <path>]
wavehold compile --run-id <id>
wavehold publish --run-id <id> [--output <path>]
```

- **scan** validates and materializes the wave into run state. It reads the
  wave JSONL, records the resolved config path, and writes
  `/app/state/wavehold/runs/<id>/wave.jsonl` and `run-meta.json`.
- **compile** walks the scanned wave through the hold-preview gates, writes
  the full rollout ledger to `/app/state/wavehold/runs/<id>/rollout-ledger.json`,
  and stages the hold witness at `/app/state/wavehold/hold-witness.json`.
- **publish** copies the compiled ledger for the run to `--output`
  (default `/app/output/mutation-rollout-atlas.json`).

`--config` defaults to `/app/config/wavehold.json`.

## Exit codes

| Code | Meaning |
|------|---------|
| `0`  | success |
| `2`  | usage / precondition failure — missing/blank `--wave`, `--run-id`, missing wave file, missing config, or a run that has not been scanned/compiled yet |
| `3`  | processing failure — the wave file is not valid JSONL, or compile hits a malformed record |

A missing `--wave` target must exit `2` at `scan`. A syntactically corrupt
wave JSONL must exit `3` at `scan`.

## Run state

```
/app/state/wavehold/runs/<id>/wave.jsonl
/app/state/wavehold/runs/<id>/run-meta.json
/app/state/wavehold/runs/<id>/rollout-ledger.json
/app/state/wavehold/hold-witness.json
/app/output/mutation-rollout-atlas.json
```

The compiled ledger persists in run state after `publish`.
