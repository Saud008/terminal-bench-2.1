# Package normalization

Every SBOM package row is normalized to norm_purl before snapshot persistence.

Rules:

1. Trim whitespace on name and version fields.
2. Lowercase the pkg scheme and type segment. Example: PKG:CARGO/foo becomes pkg:cargo/foo.
3. Canonical form is pkg:type/name@version with a single at-sign separator.
4. Duplicate raw purl values that normalize to the same norm_purl collapse to one snapshot row. Keep the lexicographically smallest raw purl as canonical_raw.
5. Snapshot packages array is sorted by norm_purl ascending.
6. staging_digest is sha256 hex over UTF-8 bytes of a canonical JSON object containing only bundle_id, packages (sorted), edges (sorted by from then to), and vex (sorted by statement_id). No whitespace outside JSON string values.

Bundle capture must never include binaries or impact rows in staging_digest input.
