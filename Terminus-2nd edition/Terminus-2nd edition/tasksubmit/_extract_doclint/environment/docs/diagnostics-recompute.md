# Diagnostics recompute (post-flush attestation)

`doclint.exportSnapshot` returns diagnostic **counts** recomputed from the flushed document text at attestation time:

| Field | Rule |
|-------|------|
| `todo_count` | Whole-word `TODO` tokens |
| `paren_delta` | `(` count minus `)` count |
| `wide_char_lines` | Lines containing any character with `len_utf16() > 1` |
| `total` | `todo_count + abs(paren_delta) + wide_char_lines` |

Counts must reflect merged text after staging flush, not the pre-merge committed buffer or a static snapshot file under `/app/fixtures/`.
