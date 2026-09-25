# Pin policy

Policy file path (default): `/app/environment/fixtures/policy/pins.json`

```json
{
  "pins": ["<hex fingerprint>", "..."],
  "stanza_allow": ["X25519"],
  "quorum_k": 1,
  "max_recipients": 3
}
```

## Evaluation order (per file)

When `parse_ok` is false → verdict `deny`, reasons include `malformed_header` only.

Otherwise apply, collecting **all** applicable deny reasons (stable sorted order at emit time):

1. `forbidden_stanza` — any stanza type whose uppercased name is not in `stanza_allow` (allow-list compared case-insensitively to the wire type).
2. `recipient_overflow` — stanza count > `max_recipients`.
3. `quorum_miss` — count of distinct stanza fingerprints that appear in `pins` is strictly less than `quorum_k`.
4. `unpinned_recipient` — at least one stanza fingerprint is absent from `pins` (recorded even when quorum already fails).

If no deny reasons remain → verdict `admit`.

## Corpus selection

- Default corpus: `/app/environment/fixtures/corpus`
- Override: environment variable `AGE_CORPUS_DIR` pointing at a directory of `*.age` files
- Policy always loads from `--policy` CLI flag (tests pass the fixture policy path)
