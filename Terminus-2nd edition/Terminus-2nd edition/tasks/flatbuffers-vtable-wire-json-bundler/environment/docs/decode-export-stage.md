# Export JSON

Stdout from `export` and `decode` is compact JSON for the staged `scene` object.

## Serialization rules

| Rule | Description |
|------|-------------|
| Tag order | Preserve wire element order at every entity depth |
| Optional fields | Omit absent fields; do not emit `null` or empty tag arrays |
| Format | Single-line compact JSON |
