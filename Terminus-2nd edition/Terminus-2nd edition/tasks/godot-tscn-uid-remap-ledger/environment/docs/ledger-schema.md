# Playtest history ledger schema

The sealed playtest export `ledger` object:

| Field | Type | Description |
|-------|------|-------------|
| `entries` | array | One record per merged relative path |
| `checksum` | string | Lowercase hex SHA-256 |

Each entry:

| Field | Type |
|-------|------|
| `path` | string — relative `.tscn` path |
| `content_sha256` | string — SHA-256 of **LF-normalized** merged content for that path |

## Checksum field

Compute over the ledger object **without** the `checksum` key:

1. Recursively sort object keys lexicographically at every nesting level.
2. Serialize with compact JSON (no extra whitespace).
3. SHA-256 the UTF-8 bytes; store lowercase hex in `checksum`.

Line ending normalization for per-file hashes and stored merged content: convert CRLF and lone CR to LF before hashing or export.
