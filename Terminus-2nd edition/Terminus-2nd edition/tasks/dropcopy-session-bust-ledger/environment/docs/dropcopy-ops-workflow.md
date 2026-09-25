# Drop-copy ops workflow — host-local session-bust control plane

This task is a **system-administration** host-local dropcopyctl drop-copy ops control plane. Operators admit offline FIX drop-copy stream fixtures into stage, enforce wire-checksum admission, sequence-reset gates, ExecID anti-duplication, bust/cancel precedence, and whole-file SQLite rollback barriers, then publish sealed compliance manifests from committed replay state only. The working baseline under /app must keep admission gates, rollback barriers, and sealed export aligned; it is not a generic service repair exercise.

There is no remote trading venue. Ops verbs are ingest (admit + stage), replay (apply barriers into SQLite), and export (seal compliance JSON from matching replay generation).

## CLI surface

Binary: `/app/bin/dropcopyctl`

```
dropcopyctl ingest --seed NAME --scenario NAME [--fixture-dir PATH]
dropcopyctl replay --scenario NAME
dropcopyctl export --scenario NAME --output PATH [--fixture-dir PATH]
```

- `ingest` requires `--seed` and `--scenario`. Optional `--fixture-dir` overrides the fixture root (default `/app/fixtures`). Reads `scenarios/<scenario>.json` and listed JSONL streams under that root.
- `replay` requires only `--scenario`. It must not require `--seed` or `--fixture-dir`. It applies rows already present in `/app/state/dropcopy-stage.json` for that scenario into `/app/work/dropcopy.db`.
- `export` requires `--scenario` and `--output`. Optional `--fixture-dir` must be accepted when present (same flag spelling as ingest) even though sealed export content comes from the SQLite ledger and generation gate, not from re-reading fixtures.

## Persistence barriers

- Ingest writes `/app/state/dropcopy-stage.json` only after full admission succeeds. Failed checksum admission must leave that path absent.
- Replay persists lifecycle rows in `/app/work/dropcopy.db` inside the SQLite table named `ledger_rows` (exact table name required).
- Replay advances generation in both `/app/state/dropcopy-stage.json` (`replay_generation`) and `/app/state/replay-generation.json`. The generation file must be a JSON object of the exact form `{"replay_generation": <integer>}` (same integer as staging). A bare integer file body or a different property name is invalid.
- Re-running `replay --scenario NAME` without a fresh ingest must remain successful: duplicate ExecIDs are skipped and the generation counter still increments by one.
- Export refuses unless staging `replay_generation` is set (> 0) and equals the `replay_generation` field in the generation file. Drift between those two values must fail export.
