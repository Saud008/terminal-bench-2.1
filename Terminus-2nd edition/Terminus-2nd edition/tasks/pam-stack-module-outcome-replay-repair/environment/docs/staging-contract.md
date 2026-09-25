# Staging contract

`pamreplay replay` is a **four-stage** pipeline before export:

1. **Flatten** — expand includes into a module list (`/app/lib/stack.sh`, `/app/docs/include-semantics.md`).
2. **Compose** — persist flatten output to `/app/work/replay.compose.json` (`/app/docs/compose-contract.md`).
3. **Stage** — copy the compose artifact to `/app/work/replay.staging.json`, then execute modules from staging only.
4. **Outcome** — persist execution results to `/app/work/replay.outcome.json`, then export from that snapshot only (`/app/docs/outcome-snapshot.md`).

## Staging file shape

UTF-8 JSON:

```json
{
  "stack_id": "001-basic-login",
  "service": "login",
  "entries": [
    {"phase": "auth", "control": "required", "module": "stubs/pam_permit.sh", "args": []}
  ]
}
```

## Invariants

- **Entry order:** `entries` must preserve flatten expansion order. Within a single phase, module order is significant for control-flag evaluation (`/app/docs/control-flags.md`). Do not reorder modules when writing or reading staging.
- **Atomic replace:** each replay run replaces the staging file entirely. Prior run entries must not be concatenated into a new staging document.
- **Execute source:** the phase machine reads only the staging artifact during module execution; do not re-flatten or re-compose mid-run.
- **Reset:** staging reset clears any prior artifact before a new run writes the next document.

The staging writer lives in `/app/lib/staging.sh`. `/app/lib/diag.sh` is diagnostic-only and is not part of the export hot path.
