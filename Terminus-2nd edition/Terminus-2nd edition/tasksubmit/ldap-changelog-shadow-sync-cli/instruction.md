Directory operators need an offline host-local shadow-sync control plane at `/app/bin/shadow-sync` that admits LDAP changelog LDIF into staging and SQLite shadow state, applies DN authenticity and modify-order gates, honors uSNChanged replay admission across retries, and seals shadow/audit export only when those ops contracts hold. There is no live directory host and no outbound network step. This is a system-administration host-local ops desk (admit → gate → seal): keep DN normalization, attribute-name canonicalization, modify ordering, changeNumber sequencing, uSNChanged replay admission, staging materialization, and sealed shadow/audit export aligned. It is not a generic software-engineering service-repair exercise, debugging task, Go-library redesign, pytest-harness workshop, or data-processing pipeline.

Ops contracts under `/app/docs/` define the enforceable invariants:

- `/app/docs/dn-normalization.md` — DN authenticity (lowercase attribute types only; preserve value case)
- `/app/docs/staging-contract.md` — staging JSONL materialization and attribute-name canonicalization
- `/app/docs/replay-idempotency.md` — uSNChanged replay admission / noop rules
- `/app/docs/export-format.md` — sealed shadow and audit JSON fields
- `/app/docs/changelog-ldif.md` — changelog LDIF record shape
- `/app/docs/cli.md` — operator verb surface and flags

Primary ops verbs:

```text
shadow-sync ingest-ldif --input PATH [--db PATH]
shadow-sync export --db /app/state/shadow.db \
  --shadow /app/output/shadow.json \
  --audit /app/output/shadow-audit.json
```

`ingest-ldif` must write `/app/state/changelog-staging.jsonl`, persist the SQLite shadow at `--db` (default `/app/state/shadow.db` when omitted), and record `/app/state/last-ingest-stats.json`. Normalized DNs must lowercase attribute types only while preserving value case. Attribute names in shadow rows, staging attrs, and `modify_ops.attr` must be lowercased; values keep source case. Records must apply in ascending `changeNumber` order even when the LDIF file lists them out of order. Modify operations within a record must apply in LDIF file order (never reorder delete ahead of add/replace). Re-ingesting already-applied `uSNChanged` values must be a noop that updates `last-ingest-stats.json` without appending staging lines or mutating shadow rows.

`export` must publish sealed shadow and audit JSON from stored shadow rows. `entry_count` and `unique_dn_count` must count distinct normalized DNs, not changelog staging lines. `max_usn` must be the maximum successfully applied `uSNChanged` across the database lifetime (including USNs whose entries were later deleted), not merely the max among live shadow rows. Exported attributes must match stored shadow rows without re-applying historical modify operations from staging. `export_sequence` advances only when the ingest immediately before export recorded `new_usns` greater than zero.

Binary path: `/app/bin/shadow-sync`. The helper package under `/app/merge` must stay off the export hot path. Bundled fixtures live under `/app/fixtures`. Hidden verifier fixtures under `/opt/verifier-fixtures` may supply DN-escape, export-count, changeNumber-order, attribute-case, and max-usn traps at runtime. After policy-module edits under `/app/internal/`, leave `/app/bin/shadow-sync` current. Do not edit `/app/docs/` or `/app/fixtures/`.
