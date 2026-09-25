# Export alignment

## verify stdout

Aligned:

```json
{"aligned": true}
```

Misaligned:

```json
{"aligned": false}
```

## Alignment checks

| Check | Requirement |
|-------|-------------|
| Ledger present | At least one ledger record exists |
| `hn55` | Ledger head equals staging envelope |
| `revision` | Ledger head equals staging envelope |
| `export_digest` | Ledger head equals digest of staged `scene` payload |
