# Compliance export schema

CLI:

```
dropcopyctl export --scenario NAME --output PATH [--fixture-dir PATH]
```

Optional `--fixture-dir` must be accepted for CLI compatibility with ingest overlays. Export must not re-admit fixture streams; sealed fields come from the `ledger_rows` table in `/app/work/dropcopy.db` and the generation gate.

## Generation file schema

`/app/state/replay-generation.json` must be a JSON object with exactly this required field:

```json
{"replay_generation": 1}
```

- `replay_generation`: non-negative integer matching the staging snapshot field of the same name after a successful replay
- Do not write a bare integer, array, or alternate key such as `generation` or `gen`

## Sealed compliance document

export writes JSON to the path passed to `--output` with:

- scenario: string
- replay_generation: integer from the `replay_generation` field of `/app/state/replay-generation.json` (must match staging)
- net_positions: map symbol to signed integer net qty
- bust_count: integer
- correction_count: integer
- cancel_count: integer
- active_exec_ids: sorted array of ExecID strings still active
- audit_digest: lowercase hex sha256 of canonical compact JSON over `net_positions` and `active_exec_ids` with sorted object keys and no insignificant whitespace

Export requires staging `replay_generation` to equal the generation file's `replay_generation` value and be greater than zero. Missing generation file, zero generation, malformed generation JSON, or drift between staging and `/app/state/replay-generation.json` must fail export (non-zero exit) without writing a successful sealed document.
