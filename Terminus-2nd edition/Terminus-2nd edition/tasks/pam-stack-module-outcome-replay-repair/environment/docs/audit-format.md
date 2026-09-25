# Audit format

For `--export /app/output/run.json`, also write `/app/output/run.audit.jsonl`.

Each line is one JSON object (UTF-8, trailing newline after each line):

```json
{"seq": 1, "phase": "auth", "module": "stubs/pam_permit.sh", "control": "required", "rc": 0}
```

Fields:

| Key | Type | Description |
|-----|------|-------------|
| `seq` | int | 1-based invocation order across the **entire replay** (never reset per phase) |
| `phase` | string | Phase name |
| `module` | string | Module path from the stack |
| `control` | string | Control flag |
| `rc` | int | Module exit code |

**Ordering requirement:** if replay fails and env rollback runs, rollback happens **before** the audit file is written. Audit lines reflect modules actually executed; the export JSON `environment` must match post-rollback state.
