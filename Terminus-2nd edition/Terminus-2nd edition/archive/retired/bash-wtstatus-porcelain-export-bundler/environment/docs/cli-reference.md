# CLI reference

On this build-and-dependency-management status-export bundler, operators invoke the host-local CLI below.

## wtstatus-export parse

```
wtstatus-export parse --porcelain PATH --config PATH --export PATH
```

Reads a porcelain v2 `-z` stream, applies `/app/config/export.json`, writes export JSON.

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Usage error or missing input |
| 1 | Parse/classify failure |

## gen_porcelain_fixture.sh

```
/app/scripts/gen_porcelain_fixture.sh --scenario NAME --seed SEED --output PATH
```

Writes a deterministic synthetic porcelain stream for catalog scenario `NAME`.
