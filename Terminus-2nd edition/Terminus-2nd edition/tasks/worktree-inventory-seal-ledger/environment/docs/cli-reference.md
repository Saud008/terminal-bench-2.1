# CLI reference

On this system-administration worktree inventory control plane, operators invoke the host-local CLI below.

## wtstatus-export parse

```
wtstatus-export parse --porcelain PATH --config PATH --export PATH
```

Admits a NUL inventory stream, applies /app/config/export.json gates, writes sealed atlas JSON.

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Usage error or missing input |
| 1 | Admission or gate failure |

## gen_porcelain_fixture.sh

```
/app/scripts/gen_porcelain_fixture.sh --scenario NAME --seed SEED --output PATH
```

Writes a deterministic synthetic inventory stream for catalog scenario NAME.
