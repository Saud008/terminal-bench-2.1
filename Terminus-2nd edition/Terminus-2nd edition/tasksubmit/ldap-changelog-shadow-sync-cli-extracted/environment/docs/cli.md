# CLI

Binary: `/app/bin/shadow-sync`

## ingest-ldif

```
shadow-sync ingest-ldif --input <path> [--db /app/state/shadow.db]
```

Reads an LDIF changelog (see `changelog-ldif.md`), normalizes DNs per `dn-normalization.md`, canonicalizes attribute names to lowercase, applies changes in ascending `changeNumber` order (not raw file order), writes `/app/state/changelog-staging.jsonl`, persists the SQLite shadow at `--db` (defaults to `/app/state/shadow.db` when omitted), and records `/app/state/last-ingest-stats.json`.

USN replay semantics are defined in `replay-idempotency.md`.

## export

```
shadow-sync export --db /app/state/shadow.db \
  --shadow /app/output/shadow.json \
  --audit /app/output/shadow-audit.json
```

Writes the shadow snapshot and audit report described in `export-format.md`. Export sequence and replay stats must reflect the ingest that immediately preceded export.

The helper package under `/app/merge` is not authoritative for export; derive exported attributes from stored shadow rows.
