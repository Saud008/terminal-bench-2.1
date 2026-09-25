# Tag precedence

Tag sets for each message are built from three sources:

1. **X-Keywords** header (comma-separated, trimmed, lowercased)
2. **Maildir flag letters** mapped to system tags (see maildir-flag-order.md)
3. **Stored notmuch tags** already present in SQLite from a prior sync

## Merge order (authoritative)

1. Start from **X-Keywords** when the header is non-empty. This list replaces any prior keyword-style tags loaded from SQLite for that message.
2. Append system tags derived from Maildir flags (flagged, seen, replied, trashed, draft).
3. Union with remaining manual notmuch tags from SQLite that are **not** keyword-style overrides.

Keyword-style tags are any tag that is not one of: `flagged`, `seen`, `replied`, `trashed`, `draft`, `inbox`.

When X-Keywords is present, it **wins** over conflicting keyword tags previously stored in the database. Do not prefer database keywords over the header.

## keywords_source field

Set `keywords_source` to `x-keywords` when the header supplied the keyword base, `db` when only database keywords were used, or `none` when no keywords apply.
