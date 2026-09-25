# Export format

## shadow.json

Path flag: `--shadow` (default `/app/output/shadow.json`)

```json
{
  "entries": [
    {
      "normalized_dn": "cn=Alice,ou=People,dc=example,dc=com",
      "attrs": { "cn": "Alice", "mail": "alice@example.com" },
      "usn_changed": 104
    }
  ],
  "entry_count": 1
}
```

- `entries` sorted by `normalized_dn` ascending.
- `entry_count` is the number of **unique** shadow entries (distinct `normalized_dn`), not changelog line count.
- Attribute values must reflect stored shadow state without re-applying historical modify operations.
- Attribute names inside each `attrs` object remain lowercased as stored at ingest.

## shadow-audit.json

Path flag: `--audit` (default `/app/output/shadow-audit.json`)

```json
{
  "unique_dn_count": 1,
  "changelog_lines_applied": 4,
  "max_usn": 104,
  "export_sequence": 1,
  "replay_stats": { "new_usns": 4, "replay_noop": 0 }
}
```

| Field | Meaning |
|-------|---------|
| `unique_dn_count` | Distinct `normalized_dn` values in shadow |
| `changelog_lines_applied` | Lines in staging JSONL |
| `max_usn` | Maximum `uSNChanged` among **all successfully applied** USNs in the database (the `usn_applied` set), including USNs for entries that were later deleted. Use `0` when no USNs have been applied. Do **not** compute this solely from live `shadow_entries` rows. |
| `export_sequence` | See `replay-idempotency.md` |
| `replay_stats` | Copied from `/app/state/last-ingest-stats.json` for the ingest immediately before this export |
