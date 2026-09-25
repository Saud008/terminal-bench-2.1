# Outcome snapshot contract

After module execution, `pamreplay replay` persists the replay outcome before export.

## Path

Fixed path: `/app/work/replay.outcome.json` (overwrite on every successful execution stage).

## CLI flow

1. Flatten stack JSON (`/app/lib/stack.sh`).
2. Compose flatten output to `/app/work/replay.compose.json` (`/app/lib/compose.sh`).
3. Stage compose artifact to `/app/work/replay.staging.json` (`/app/lib/staging.sh`).
4. Execute modules from staging only (`/app/lib/runner.sh`).
5. Write outcome snapshot from execution results (`/app/lib/outcome.sh`).
6. Validate outcome invariants (`/app/lib/outcome_guard.sh`; `/app/docs/outcome-guard.md`).
7. Export reads the validated outcome snapshot only — it must not re-execute modules or re-flatten the stack.
## Schema

```json
{
  "version": 1,
  "stack": "/app/fixtures/stacks/001-basic-login.json",
  "user": "alice",
  "exit_code": 0,
  "phases": [
    {"phase": "auth", "status": "ok", "modules_run": 1}
  ],
  "environment": {"ROLE": "login"},
  "audit_path": "/app/output/001-basic-login.audit.jsonl"
}
```

- `version`: outcome snapshot schema version, always the integer `1`; export reads this field to confirm a compatible snapshot before copying the remaining fields.
- `stack`: absolute path to the stack JSON file exactly as supplied to replay (the resolved `--stack` argument); recorded verbatim in the snapshot and copied to export.
- `phases`: one object per phase attempted, in **execution order** (not sorted alphabetically).
- `environment`: committed variables after rollback, if any.
- `audit_path`: sibling audit JSONL path derived from `--export`.

Missing outcome snapshot must cause export to fail with non-zero exit. Export must copy snapshot fields into the final JSON document without reordering phases or re-reading staging.

Implementation lives in `/app/lib/outcome.sh` and `/app/lib/export.sh`.
