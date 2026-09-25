# Merge snapshot (`/app/state/merge-snapshot.json`)

```json
{
  "groups": [ /* same shape as report groups */ ],
  "rejected": [ /* same as report */ ],
  "snapshot_digest": "<sha256 hex>"
}
```

`snapshot_digest` is SHA-256 hex of the UTF-8 bytes of compact JSON `{"groups":[...],"rejected":[...]}` where `groups` and `rejected` are sorted by `merge_key` / `line` respectively (stable lexicographic), with separators `,` and `:` and no whitespace. Object keys inside each group/rejected entry must appear in declaration order (`merge_key`, `talker`, `sentence`, `multipart_total`, `fragments_merged`, `payload_fields`, `utc_iso` for groups; `line`, `reason` for rejected) — do not alphabetize keys when hashing.

## Export gate

`export::staging::publish_export` reads the snapshot, verifies `snapshot_digest` via `export::writer::verify_digest`, runs `export::validate::validate_snapshot`, and writes the merge report through `export::wrap::build_report` using snapshot fields only.

`export::validate::validate_snapshot` requires each group's `merge_key` to begin with `{talker}:`. Incomplete multipart groups (`fragments_merged < multipart_total`) are allowed in single-pass snapshots.
