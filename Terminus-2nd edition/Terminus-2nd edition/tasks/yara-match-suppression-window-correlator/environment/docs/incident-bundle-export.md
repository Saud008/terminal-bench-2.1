# Sealed incident bundle export

Export writes /app/output/incident-bundle.json as a trust-bound artifact:

- correlate_generation: from correlate-generation.json generation field
- staging_generation: from staging snapshot
- incidents: sorted by detected_ms then event_id
- bundle_digest: sha256 of normalized bundle body

## bundle_digest

`bundle_digest` is the lowercase hex SHA-256 of the canonical JSON encoding of the bundle after the `bundle_digest` key is removed entirely (the key must be absent, not present with an empty or placeholder value).

### Recursive normalization

Before hashing, normalize the payload recursively:

1. **Objects (dictionaries):** sort keys lexicographically at every nesting depth; normalize each value recursively. Top-level-only key sorting is not sufficient.
2. **Arrays (lists):** preserve element order; normalize each element recursively so nested objects inside arrays still receive sorted keys.
3. **Numbers:** when a float equals an integer value (for example `1.0`), coerce it to an integer before serialization; leave non-integral floats unchanged. Apply this rule at every nesting depth.
4. **Scalars:** strings, booleans, and null pass through unchanged.

### Serialization

Marshal the normalized payload as compact JSON with sorted object keys and separators comma and colon (no spaces, no pretty-printing). Nested objects must already be key-sorted by the recursive normalize step so the hashed byte sequence is fully determined at every depth.

SHA256 the UTF-8 bytes and encode as lowercase hex (64 characters).

## Export gates

Export fails when correlate_generation is zero.

Export recomputes events_digest from staged events and rejects when it differs from event-staging.json events_digest.
