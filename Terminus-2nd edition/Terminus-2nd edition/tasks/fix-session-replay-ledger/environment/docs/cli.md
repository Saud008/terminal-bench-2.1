# CLI

Binary: `/app/bin/fix-ledger`

## ingest

```
fix-ledger ingest --session-dir <dir> --db /app/state/ledger.db
```

Reads `*.fix` files in lexical path order, validates checksums, persists executions, writes `/app/state/ingest-staging.json`. Prints `ingested=<N>` where N is newly inserted rows.

## export

```
fix-ledger export --db /app/state/ledger.db --out /app/output/positions.json
```

Replays persisted executions in contract order and writes positions JSON. Prints `exported=<symbol_count>`.
