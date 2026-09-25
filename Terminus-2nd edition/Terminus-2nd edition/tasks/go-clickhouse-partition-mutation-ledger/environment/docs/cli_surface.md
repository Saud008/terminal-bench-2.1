# chmutled CLI surface

Binary path: /app/bin/chmutled

## reconcile-partitions

```
chmutled reconcile-partitions --metadata-dir DIR --mutations-dir DIR --replica-dir DIR --config-dir DIR --staging PATH
```

Reads partition metadata, mutation commands, and replica logs plus configuration, writes staging JSONL to PATH.

## emit-readiness

```
chmutled emit-readiness --staging PATH --sqlite PATH --atlas PATH
```

Reads staging JSONL, upserts idempotent rows into SQLite, writes readiness atlas JSON.
