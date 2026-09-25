# lootsettle CLI surface

Binary: /usr/local/bin/lootsettle

```
lootsettle ingest --season PATH --events PATH
lootsettle settle --seasons-dir PATH
lootsettle export --output PATH
lootsettle replay --season PATH --events PATH --seasons-dir PATH --output PATH
```

Defaults:

| Flag | Default |
|------|---------|
| --season | /app/fixtures/seasons/winter-alpha.json |
| --events | /app/fixtures/events/alpha-stream.jsonl |
| --seasons-dir | /app/fixtures/seasons |
| --output | /app/output/settlement-report.json |

ingest validates signatures and writes staging. settle consumes staging and updates ledger, processed-events, replay-generation. export validates gates and writes the report. replay runs ingest, settle, export in order.

After authenticity-policy edits under /app/crates/lootsettle-core/, leave /usr/local/bin/lootsettle current.
