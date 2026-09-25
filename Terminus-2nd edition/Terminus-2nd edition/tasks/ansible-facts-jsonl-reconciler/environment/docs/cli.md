# facts-chain CLI

```
facts-chain reconcile --jsonl <path> --run-id <id>
facts-chain stage --run-id <id>
facts-chain export --run-id <id> --out <path>
```

All subcommands require `--run-id`. Reconcile ingests JSONL; stage reads `facts.db`; export writes the diff report.

Environment:

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_ROOT` | `/app` | Application root |
| `FACTS_DB` | `/app/state/facts.db` | SQLite ledger |

Exit non-zero on validation or schema errors.
