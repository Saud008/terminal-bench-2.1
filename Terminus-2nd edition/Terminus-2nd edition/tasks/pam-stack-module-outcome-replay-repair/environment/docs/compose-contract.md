# Compose contract

After flattening (`/app/lib/stack.sh`), `pamreplay replay` **composes** the flattened stack into `/app/work/replay.compose.json` before staging.

## Artifact shape

Same top-level fields as flatten output:

```json
{
  "stack_id": "001-basic-login",
  "service": "login",
  "entries": [ ... ]
}
```

## Invariants

- **Entry order:** `entries` must match flatten expansion order byte-for-byte in sequence. Within a phase, module order is significant for control-flag evaluation (`/app/docs/control-flags.md`). Do not sort entries by phase, module path, or control name when composing.
- **Atomic replace:** each replay run replaces the compose file entirely. Prior compose documents must not be merged with new flatten output.
- **Reset:** `pamreplay_compose_reset` clears any prior compose artifact before the next write.
- **Downstream:** `/app/lib/staging.sh` reads the compose artifact only — it must not re-flatten or re-read the stack JSON during staging.

Implementation lives in `/app/lib/compose.sh`.
